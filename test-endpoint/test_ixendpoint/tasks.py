#!/usr/bin/python3
from __future__ import absolute_import, unicode_literals

import subprocess
import logging
import socket
import json
import test_common.commands as EndPointCommands
import test_common.interface as interface
import test_common.celeryconfig as config

from time import sleep
from celery import Celery
from subprocess import Popen
from multiprocessing import Manager
from test_common.util import Util
from test_common.timer import pTimer
from test_ixendpoint.sock import sock
from test_ixendpoint.usageStats import usageStats


logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

dev_key = Util.getDeviceKey()

queue = 'testendpoint.' + dev_key

app = Celery('tasks', broker=config.broker)

app.config_from_object('test_ixendpoint.celeryconfig')

route_key = 'test.tasks.testendpoint.' + dev_key

app.conf.task_routes = {route_key: {'queue': queue}}

logger.info("****  task thread broker mq %s ****" % config.broker)

hostName = socket.gethostname()
manag = Manager()
    
usage=None
sockClient = None
sockDump = None
process = None
client = None
measureCPU = None
measurePackets = None
usageTimer = None
deviceStatusTimer = None
dumpTimer = None
gSessionKeys = manag.list()
key = ""
addr4 = ""
err = ""
err_no = 0
counter_id=0




class tasks:
    @app.task
    def startApp(program, system, test_id):
        logger.info("********  Start process %s" % program)
        global process
        global err_no
        global client
        global sockClient
        global sockDump
        global usage
        global dumpTimer

        err_no = 0

        try:

            tasks.runCmdWait(program)

            if (system == 'gateway'):
                logger.info("********  Running jumpnet-gateway post install commands {0}".format(EndPointCommands.Command_forward_all_gateway))
                tasks.runCmdWait(EndPointCommands.Command_forward_all_gateway)
                # setup dump socket
                sockDump = sock('jumpnet-gateway', dump=True)
                dumpTimer = pTimer(1, 60*3, True, False, tasks.DumpListenerTimer, program, system, test_id)
                

            elif (system == 'client'):
                logger.info("********  Running jumpnet-client post install commands {0}".format(EndPointCommands.Command_forward_all_client))
                tasks.runCmdWait(EndPointCommands.Command_forward_all_client)

            # start usage stats
            usage = usageStats(hostName, system, test_id)

            

            tasks.SendReply('startApp', program, 'Success', '')
        except Exception as e:
            logger.error("Error: {0}".format(e))
            tasks.SendReply('startApp', program, 'Error', e)

    @app.task
    def startClientd(program, system, test_id):
        logger.info("********  Start process %s" % program)
        global process
        global err_no
        global client
        global sockClient

        err_no = 0

        try:
            process = Popen([program], shell=True, bufsize=1, universal_newlines=True)
            sleep(2)

            # todo  figure later to get endpoint name could be multiple endpoints, possibly pass in from the orch
            sockClient = sock('jumpnet-client')

            tasks.SendReply('startClient', program, 'Success', '')
        except Exception as e:
            logger.error("Error: {0}".format(e))
            tasks.SendReply('startClient', program, 'Error', e)

    @app.task
    def sendAction(action, system, test_id):
        try:
            logger.info("********  Send action %s" % action)

            if action[0] == 'Exit':
                logger.info("********  Send action pkill clientd")
                if sockClient is not None:
                    sockClient.Send(interface.InterfaceExit)
                else:
                    tasks.runCmdWait(command_exit_jumpnet_client)
            else:
                if process is not None:
                    global key
                    global addr4
                    global err
                    global err_no

                    key = ""
                    addr4 = ""

                    command = action[0]  
                    op = action[1]
                    payloadType = action[2]  
                    

                    # todo move interface enable message to only use messageTypes and change commands in play-by-play scripts
                    # and also can get rid payloadtype since we really don't use it
              
                    message = interface.command[op].format(payload=payloadType)

                    logger.info("Send Action message {0}".format(message))

                    sockClient.SendWait(message)

                    logger.info('got response...{0}'.format(message))

            tasks.SendReply(action,  interface.command[action], 'Success', '')
        except Exception as e:
            logger.error("Error: {0}".format(e))
            tasks.SendReply(action,  interface.command[action], 'Error', e)

    @app.task
    def sendControlSocket(action, system, test_id):
        global sockClient
        global sockDump
        global measureCPU
        global measurePackets
        global usageTimer
        global deviceStatusTimer
        global dumpTimer
        global counter_id
        status='Success'
        message=''

        try:
         
            command = action[0]  
            endpoint = action[1]

            logger.info("********  Control socket command {0} {1}".format(command, endpoint))

            if (sockClient is None and endpoint == 'gateway'):
                logger.info("********  Running jumpnet-gateway start control socket")
                sockClient = sock('jumpnet-gateway')

                #  start measuring system
                # measureCPU = MeasureSystem('CPU', '')
                # measurePackets = MeasureSystem('packets', 'tun0')

            if (command == 'UsageStats'):
                usageTimer = pTimer(5, 120, True, False, tasks.UsageStatsTimer, usage, command, endpoint, test_id)

            if (command == 'PolicySet'):

                if len(gSessionKeys) > 0:
                    counter_id+=1
                    logger.info("Start Dump timer..... ")
                   
                   
                    for key in gSessionKeys:
                        message = interface.PolicySet.format(session=key,counter_id=counter_id,client_scheduler=action[3],gateway_scheduler=action[4],policy=action[1],version=action[2])
                        data = sockClient.Send(message)
                        usage.addOPEvent(message)

                else:
                    status='Error'
                    message='PolicySet not set, no sessions available'
                    logger.info("********  PolicySet failed, no sessions available ")

            if (command == 'TrafficControl'):
                payload = action[1]
                counter_id+=1

                for key in gSessionKeys:
                    message = interface.TrafficControl.format(session=key, payload=payload)
                    data = sockClient.Send(message)
                    usage.addOPEvent(message)

            if (command == "DeviceStatus"):
                if (endpoint == 'gateway'):
                    deviceStatusTimer = pTimer(5, 120, True, False, tasks.RequestDumpSocketTimer, command)
                else:
                    deviceStatusTimer = pTimer(5, 120, True, False, tasks.UsageStatsTimer, usage, command, endpoint, test_id)


            # elif ('StatsRawRequest' in interface.messageTypes[action]):
            #    usageRawTimer = threading.Timer(5.0, tasks.UsageStatsTimer, (action,))
            #    usageRawTimer.start()

            tasks.SendReply(command, interface.messageTypes[command], status, message)
        except Exception as e:
            logger.error("Error: {0}".format(e))
            tasks.SendReply(action, interface.messageTypes[command], 'Error', e)

    @app.task
    def start(program, system, test_id):
        try:
            if 'iperf3 -J' in program:
                key = ""
                try:
                    if 'client' in system:
                        response, key = sockClient.getMessage('session', '', '', 5)
                        if response is False:
                            tasks.SendReply('start', program, 'Error', 'session not created')
                            logger.info("********  No session created, not starting  process %s" % program)
                            return

                        program = '{0} -k {1}'.format(program, key)
                except Exception as e:
                    logger.error("***************   Error    ******** ")
                    logger.error(e)
                    key = ""

            logger.info("********  Start process %s" % program)
            Popen([program], shell=True, bufsize=1, universal_newlines=True)

            tasks.SendReply('start', program, 'Success', '')
        except Exception as e:
            logger.error("Error: {0}".format(e))
            tasks.SendReply('start', program, 'Error', e)

    @app.task
    def stop(action, system, test_id):
        global sockClient
        global sockDump
        global dumpTimer
        global usageTimer

        try:
            
            if ('gateway' in system):
                logger.info("********  Running jumpnet-gateway stop commands {0}".format(EndPointCommands.Command_stop_all_gateway))
                tasks.runCmdWait(EndPointCommands.Command_stop_all_gateway)

                # cancel timers
                tasks.removeObjects()

                # usageRawTimer.stop()

                # delete measure objects
                # del mesaureCPU
                # del mesaurePackets


            elif ('client' in system):
                logger.info("********  Running jumpnet-client stop commands {0}".format(EndPointCommands.Command_stop_all_client))
                tasks.removeObjects()

                tasks.runCmdWait(EndPointCommands.Command_stop_all_client)
                # cancel timers
                # usageRawTimer.stop()

            elif ('server' in system):
                logger.info("********  Running server stop commands {0}".format(EndPointCommands.Command_stop_all_server))
                tasks.runCmdWait(EndPointCommands.Command_stop_all_server)

            tasks.SendReply('stop', system, 'Success', '')

        except Exception as e:
            logger.error("Error: {0}".format(e))
            tasks.SendReply('stop', system, 'Error', e)

    @app.task
    def registerClient(type, queue, route, hostname):
        logger.info('\n'.join([
            "*" * 25,
            "Client Registering => {} {} {}".format(type, queue, route),
            "*" * 25,
            "",
        ]))
        logger.info("\n**********************   \n  Client Registering => " + type + " " + queue + " " + route + " \n*********************************\n")

    def runCmd(command):
        try:
            process = subprocess.Popen(command, shell=True, universal_newlines=True)
        except Exception as e:
            logger.error("***************   Error    ******** {0}".format(e))
            logger.error(e)

    def runCmdWait(command):
        try:
            process = subprocess.Popen(command, shell=True, universal_newlines=True)
            process.wait()
        except Exception as e:
            logger.error("***************   Error    ******** {0}".format(e))
            logger.error(e)

    def SendReply(action, command, status, msg):
        try:
            taskName = 'test_orchestrator.tasks.endpointReply'
            app.send_task(taskName, [action, command, status, msg], queue='testorchestrator', routing_key='test.tasks.testorchestrator')

        except Exception as e:
            logger.error("Error: {0}".format(e))
            logger.error(e)

    def removeObjects():
        global sockClient
        global sockDump
        global dumpTimer
        global usageTimer
        global usage
        global deviceStatusTimer

        try:

            if sockClient:
                del sockClient
                sockClient = None

            if sockDump:
                del sockdump
                sockDump = None
            
            if usageTimer: 
                usageTimer.stop()
                del usageTimer
                usageTimer = None

            if dumpTimer:
                dumpTimer.stop()
                del dumpTimer
                dumpTimer = None

            if usage:
                del usage
                usage = None

            if deviceStatusTimer:
               deviceStatusTimer.stop()
               del deviceStatusTimer
               deviceStatusTimer = None

        except Exception as e:
            logger.error("Error: {0}".format(e))
            logger.error(e)

    def UsageStatsTimer(usage=None, action='stopTimer', endpoint='', test_id=''):
        global gSessionKeys

        try:

            if sockClient:
                response, payload = sockClient.getMessage(action, '', '', 5)
                logger.info("Process json output..")

                if (action == 'UsageStats'):
                    usage.addEvents(action, payload, 'session')
                    gSessionKeys = usage.getSessionKeys()
                else:
                    usage.addOPEvent(payload)
                
            
            
        except Exception as e:
            logger.error("Error: {0}".format(e))
            return False

    def RequestDumpSocketTimer(action):
        global gSessionKeys

        try:
           
            message = sockClient.buildMessage(action)
            data = sockClient.Send(message)
           
        except Exception as e:
            logger.error("Error: {0}".format(e))
            return False


    def DumpListenerTimer(action='stopTimer', endpoint='', test_id=''):
        global counter_id
        global dumpTimer
        global sockDump

        try:

            if sockDump:

                data = sockDump.waitResponse()
                logger.info("Dump Response: {0}".format(data))
                if data:
                    
                    json_data = json.loads(data)
                    if json_data['op'] == 'Policy.SetResponse':
                        if json_data['payload']['counter'] == str(counter_id):    
                            tasks.SendReply(json_data['op'], endpoint, 'Success', '')
     

                    if json_data['op'] == 'Subflow.TCResponse':
                        if json_data['payload']['counter'] == str(counter_id):
                            tasks.SendReply(json_data['op'], endpoint, 'Success', '')

                    if json_data['op'] == 'Device.HostStatus':
                        usage.addOPEvent(data)
          


            if action == 'stopTimer':
                del dumpTimer
                dumpTimer = None
                del sockDump
                sockDump = None
                       

            # todo add reply when we get the right indication that all sessions policies are set
        except Exception as e:
            logger.error("Error: {0}".format(e))
            return False

    
