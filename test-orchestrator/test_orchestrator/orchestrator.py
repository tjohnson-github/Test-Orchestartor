import sys
import os
import signal
import threading
import time
import logging
import uuid
import test_orchestrator.tasks
import test_common.commands as TestCommands
import test_common.interface as interface
import test_common.celeryconfig as config

from time import sleep
from celery import Celery
from celery.bin import worker
from test_orchestrator.tasks import tasks  # noqa
from test_common.database import database
from test_common.util import Util

app = Celery('tasks', broker=config.broker)
app.config_from_object('test_orchestrator.celeryconfig')

api_key = os.environ['API_KEY']
test_id = uuid.uuid4()
test_key =''

logger = logging.getLogger(__name__)


if (len(sys.argv) == 2):
    test_key = sys.argv[1]
    logger.info("****  TEST_ID created {0} ****".format(test_id))
   
else:
    if len(sys.argv) < 8:
        logger.info("****  Usage: python3 trigger.py <remote task> <test name> <number of clients> <tier name> <GW tier name> <packages> <protocol> <download/upload> ****")
        logger.info("****  Example: python3 trigger.py test_orchestrator.tasks.startTest test-cell.txt 10  test.v6.tsdn.io test.v6.tsdn.io udp  development****")
        workerExit(test_id, '', '', 'Invalid number of arguments')



class orchestrator():
    def main():
        test = True
        clientIteration = 0
        maxTimeOut = 5 * 60  # add 5 minute timeout value
        timeOut = 0
        reason = ''
        testName='test-cell'
        numClients = 1
        tier = 'tsdn.io'
        gwTier = 'tsdn.io'
        protocol = 'tcp'
        test_mode = 'download'
        packageList = 'candidate'
        encryption = 'ON'
        commit_hash = ''
        branch_name = ''


        try:
            logging.basicConfig(level=logging.INFO)

            logger.info("****  orchestrator thread start %s ****" % os.getcwd())
            logger.info("****  orchestrator thread broker MQ %s ****" % config.broker)

            logger.info("Test Starting... {0} ".format(testName))

            # this still here for backwards compatiblilty. Will soon be depricated 
            if len(sys.argv) > 2:
                # get arguments passed in          Examples
                testName = sys.argv[1]             # test-cell
                numClients = int(sys.argv[2])      # 2
                tier = sys.argv[3]                 # tsdn.io 
                gwTier = sys.argv[4]               # tsdn.io
                protocol = sys.argv[5]             # tcp or udp
                test_mode = sys.argv[6]            # download or upload
                encryption = sys.argv[7]           # on or off
                if len(sys.argv) >= 9:
                    packageList = sys.argv[8]      # jumpnet-client_4.0.2.0.38736,jumpnet-gateway_4.0.2.0.38736
                if len(sys.argv) >= 10:  
                    commit_hash = sys.argv[9]      # commit hash
                if len(sys.argv) >= 11:
                    branch_name = sys.argv[10]     # master

                # get commands
                testCommands = Util.readConfig(testName)

            else:
                # get commands from API
                testConfig, OpCommands = Util.getTestConfig(test_key)

                logger.info("Config: {0}".format(testConfig))
                logger.info("Config: {0}".format(OpCommands))

                testName = testConfig['name']
                numClients = testConfig['num_clients']

                testCommands, packageList = Util.getTestCommands(OpCommands)
                for cmd in testCommands:
                    logger.info("Command: {0}".format(cmd))


            logger.info("Test Starting... {0} {1} {2} {3} {4} {5} {6} {7} {8} {9}".format(
                testName, numClients, tier, gwTier, packageList, protocol, test_mode, encryption, commit_hash, branch_name))

            # create result record
            db = database('testtier')
            if not (db.connect()):
                workerExit(test_id, '', '', 'Database Failed')

            client_version, gateway_version, packageList = Util.getPackages(packageList)
            db.AddResults(test_id, testName, numClients, tier, gwTier, gateway_version, client_version, protocol, test_mode, encryption, test_key)

            resp = Util.update_status(test_key, 'assigning', 'test-orchestrator', 'success')
            if resp and resp.status_code!=200:
                logger.error("REST API Error {0}".format(resp))


            # get number of clients either from command list or overide from arguments
            numClients = orchestrator.getNumClients(testCommands, numClients)

            # start test
            test = True

            while test and timeOut < maxTimeOut:
                # check to see enough endpoints are up and wait here until enough nodes registered or time out
                enoughClients, gateway_node = Util.checkClients(numClients)
                if enoughClients:

                    resp = Util.update_status(test_key, 'running', 'test-orchestrator', 'success')
                    if resp and resp.status_code!=200:
                        logger.error("REST API Error {0}".format(resp))

                    tier = orchestrator.getTier(testCommands, tier)
                    gwTier = orchestrator.getGatewayTier(tier, gwTier, gateway_node)
                    if testCommands:
                        reportFile = '/tmp/iperf-{0}-{1}'.format(testName, time.strftime("%Y%m%d-%H%M%S"))

                        # go through and make sure no processes are hanging around to mess up the test
                        orchestrator.CleanUpClients(test_id)

                        logger.info("****** Start Test {0} {1} {2} {3}".format(test_id, numClients, gwTier, packageList))

                        for commands in testCommands:
                            logger.info("****** Command {0}".format(', '.join(map(str, commands))))
                            clientIteration = 0

                            for key, value in Util.Clients.items():
                                isEndpoint = value[0]

                                logger.info("***  Client => Key: %s Values: %s" % (key, value))

                                if commands[0] == 'Sleep':
                                    # collectionItems = format(' '.join(map(str, commands[1:])))
                                    # sleepTask(commands[1], collectionItems)
                                    sleep(int(commands[1]))
                                    break

                                if commands[0] == 'clients':  # this is for number of clients
                                    break

                                # todo not sure if I need this anymore , might be depricated
                                #  this for incrementing the phone account for each client
                                #  So that each clientd is logged in with a different account
                                if isEndpoint == 1:
                                    clientIteration += 1

                                # Build the message to be remotely executed
                                orchestrator.buildTask(clientIteration, reportFile, commands, value, key, test_id, numClients, tier,
                                                       gwTier, protocol, test_mode, packageList, testName, encryption)

                        # end of commands for test so exit test
                        test = False
                        reason = 'Test Completed'
                    else:
                        logger.error('Error: Test file not found')
                        test = False
                        reason = 'Incorrect test name'

                else:
                    logger.info('Waiting for enough endpoints....')

                logger.info("****  Queue Length => %d %s" % (len(Util.gClients),  test))

                timeOut += 2
                sleep(2)
        except Exception as e:
            logger.error("***************   Error    ******** " + e)
            logger.error(e)
            reason = 'Error: Exception'

        # finished test
        orchestrator.CleanUpClients(test_id)

        if test is True:
            reason = 'Test timed out. Only {0} endpoints registered'.format(len(Util.gClients))

        workerExit(test_id, test_mode, encryption, reason, commit_hash, branch_name)
        exit(0)

    def CleanUpClients(test_id):
        try:
            for key, value in Util.Clients.items():
                isEndpoint = value[0]
                mqueue = value[1]

                if isEndpoint == 1:
                    system = 'client'
                elif isEndpoint == 0:
                    system = 'server'
                else:
                    system = 'gateway'

                task = TestCommands.registeredTask[system]['Start']
                command = TestCommands.command_clean
                logger.info('****  Sending task {0} {1} {2} {3}'.format(task, command, mqueue, key))
                app.send_task(task, [command, system, test_id], queue=mqueue, routing_key=key)
        except Exception as e:
            logger.error(e)

        return

    
    def buildTask(phoneAccount, reportFile, commands, valueList, route, test_id, numClients, tier, gwTier, protocol, test_mode, packageList, testName, encryption):


        try:

            isEndpoint = valueList[0]
            mqueue = valueList[1]

            if isEndpoint == 1:
                system = 'client'
                hostname = valueList[2][1]
                dev_key = valueList[3]

                # start jumpnet-client
                if commands[0] == 'JumpnetClient':
                    clientName = 'jumpnet-client'
                    phoneAccount = 'testbed'

                    # add route ip to iperf server. jumpnet client will use this to do an add route
                    traffic_route = Util.get_ip_address_byname(tier, hostname)

                    if encryption == 'ON':
                        # add encryption option
                        JumpnetClientCommand = TestCommands.command_jumpnet_client + ' ' + TestCommands.command_jumpnet_client_encryption
                    else:
                        JumpnetClientCommand = TestCommands.command_jumpnet_client

                    command = JumpnetClientCommand.format(client_name=clientName, dev_key=dev_key, gateway_ip=gwTier,
                                                           api_key=api_key, jumpnet_user=phoneAccount, route_ip=traffic_route)

                # start iperf client
                elif commands[0] == 'IperfClient':
                    # set test mode option -R for reverse / download mode or empty is upload mode
                    if test_mode == 'download':
                        _test_mode = '-R'
                    else:
                        _test_mode = ''

                    #  host ID
                    host_id = uuid.uuid4()
                    traffic_route = Util.get_ip_address_byname(tier, hostname)
                    if protocol == 'udp':
                        command = TestCommands.command_iperf_udp.format(download=_test_mode, server=traffic_route, duration=commands[1], module=interface.ixcassModule,
                                                                        test_id=test_id, host_id=host_id, test_name=testName, num_clients=numClients, tier=gwTier)
                    else:
                        command = TestCommands.command_iperf_tcp.format(download=_test_mode, server=traffic_route, duration=commands[1], module=interface.ixcassModule,
                                                                        test_id=test_id, host_id=host_id, test_name=testName, num_clients=numClients, tier=gwTier)

                # start generic process
                elif commands[0] == 'Start' and commands[1] == system and commands[2] == 'process':
                    command = format(' '.join(map(str, commands[3:])))

                # Run command to Add ip route
                elif commands[0] == 'Client' and commands[1] == 'addroute':
                    traffic_route = Util.get_ip_address_byname(tier, hostname)
                    command = TestCommands.command_addroute.format(traffic_route)

                # run control socket command
                elif commands[0] == 'SubflowEnable':
                    command = commands

                # stop test and exit any pending running apps on client
                elif commands[0] == "Stop":
                    command = commands[0]

                # run s3cmd / this was initially for file archiving reports from iperf
                elif commands[0] == 'S3cmd':
                    command = TestCommands.command_s3cmd.format(commands[0], reportFile, commands[1], system, reportFile[5:])

                # install client package
                elif commands[0] == 'Install' and 'client' in commands[1]:
                    name, version = Util.getPackage(commands[1], packageList)
                    if version != "":
                        command = TestCommands.command_install_package_version.format(name, version)
                    else:
                        command = TestCommands.command_install_package.format(name)

                # start collecting usage stats
                elif commands[0] == 'UsageStats' and commands[1] == system:
                    command = [commands[0], commands[1]]

                # start collecting usage raw stats
                elif commands[0] == 'UsageRaw' and commands[1] == system:
                    command = [commands[0], commands[1]]

                # start collecting cpu/mem stats
                elif commands[0] == 'DeviceStatus' and commands[1] == system:
                    command = [commands[0], commands[1]]

                else:
                    # logger.info("Command %s not for client" % commands[0])
                    return

            elif isEndpoint == 0:

                system = 'server'

                # start iperf server
                if commands[0] == 'IperfServer':
                    #  host ID
                    host_id = uuid.uuid4()
                    command = TestCommands.command_iperf_server.format(module=interface.ixcassModule, test_id=test_id, host_id=host_id,
                                                                       test_name=testName, num_clients=numClients, tier=gwTier)

                # start generic server process
                elif commands[0] == 'Start' and commands[1] == 'ixendpoint' and commands[2] == 'process':
                    command = format(' '.join(map(str, commands[2:])))

                # stop test and exit any pending running apps on server
                elif commands[0] == 'Stop':
                    command = commands[0]

                # run s3cmd / this was initially for file archiving reports from iperf
                elif commands[0] == 'S3cmd':
                    command = TestCommands.command_s3cmd.format(commands[0], reportFile, commands[1], system, reportFile[5:])

                else:
                    # logger.info("Command %s not for ixendpoint" % commands[0])
                    return

            elif isEndpoint == 2:
                system = 'gateway'

                # start collecting usage stats gateway
                if commands[0] == 'UsageStats' and commands[1] == system:
                    command = [commands[0], commands[1]]

                # start collecting usage raw stats gateway
                elif commands[0] == 'UsageRaw' and commands[1] == system:
                    command = [commands[0], commands[1]]

                 # start collecting cpu/mem stats
                elif commands[0] == 'DeviceStatus' and commands[1] == system:
                    command = [commands[0], commands[1]]

                # install gateway package
                elif commands[0] == 'Install' and 'gateway' in commands[1]:
                    name, version = Util.getPackage(commands[1], packageList)
                    if version != "":
                        command = TestCommands.command_install_package_version.format(name, version)
                    else:
                        command = TestCommands.command_install_package.format(name)

                # stop test and exit any pending running apps on server
                elif commands[0] == 'Stop':
                    command = commands[0]

                elif commands[0] == 'TrafficControl':
                    control_file= commands[1]
                    payload = Util.fileToJson(control_file)
                    command = [commands[0], payload]

                elif commands[0] == 'PolicySet':
                    command =  commands
                
                elif commands[0] == 'PolicyWait':
                    command = commands[0]
                    # todo I think initially I will put in wait for queue code to wait for x seconds 
                    # for queue message from response from PolicySet. PolicySet already sets up Dump socket and will send response back
                    status = orchestrator.WaitForTask(30)
                    return 
                else:
                    # logger.info("Command %s not for gateway" % commands[0])
                    return

            else:
                logger.error("Invalid Enpoint type: {0}".format(isEndpoint))
                return

            logger.info('Getting Task....{0} {1} {2}'.format(system,commands[0], TestCommands.registeredTask))
            task = TestCommands.registeredTask[system][commands[0]]
            logger.info('Ready to Send...{0}'.format(task))
            logger.info('****  Sending task {0} {1} {2} {3} {4}'.format(phoneAccount, task, command, mqueue, route))
            app.send_task(task, [command, system, test_id], queue=mqueue, routing_key=route)
        except Exception as ex:
            logger.error("Error: {0}".format(ex))

        return

    def sleepTask(sleepDuration, collectionItems):
        timeToSleep = int(sleepDuration)
        i = 0
        while i < timeToSleep:
            sleep(1)
            i += 1

    def WaitForTask(timeout):
      status=''
      count=0

      while not status and count < timeout: 

        try:
          status = Util.messageQueue.get(False) 
    
        except Exception as e:
          logger.info("****  message queue Empty ****")
   
        count+=1
        sleep(1)


      return status

    def getGatewayTier(tier, gwTier, gateway_node):
        if gwTier:
            gwTier = gwTier
            if gwTier in tier:
                gwTier = Util.get_ip_address_byname(tier, gateway_node)
        else:
            gwTier = Util.get_ip_address_byname(tier, gateway_node)

        return gwTier

    def getTier(commands, tier):
        # set internal vs external routing hostname lookup {0} gets replaced with hostname so it can get the internal or external ip
        if not tier:
            if len(commands[0]) > 2:
                tier = commands[0][2]
            else:
                tier = 'tsdn.io'

        return tier

    def getNumClients(commands, numClients):
        # check for global numclients from trigger if not overriden then use config option and set number of clients
        if numClients == 0:
            if 'Clients' in commands[0] and len(commands) > 1:
                numClients = int(commands[0][1])
            else:
                numClients = 1
        else:
            numClients = numClients

        return numClients


def workerExit(test_id, test_mode, encryption, reason, commit_hash='', branch_name=''):
    if 'Database Failed' in reason:
        db = None
    else:
        # update results
        db = database('testtier')
        if db.connect():
            # added any errors from nodes
            if Util.gErrors:
                reason = ', '.join(map(str, Util.gErrors))

            result = db.UpdateResults(test_id, test_mode, reason)
            # set test_id back to cosole so reporting can pick it up
            Util.runCmd("echo " + result['result'] + " > result")
            Util.runCmd("echo " + result['error_text'] + " > error_text")

            resp = Util.update_status(test_key, result['result'] , 'test-orchestrator', result['error_text'])
            if resp and resp.status_code!=200:
                logger.error("REST API Error {0}".format(resp))

        else:
            db = None

    Util.runCmd("echo " + str(test_id) + " > testid")

    # send notification to slack
    Util.slackNotification(db, encryption, test_id, commit_hash, branch_name)

    # terminate any celery worker threads
    Util.runCmd("sudo pkill -f -TERM test-orchestrator")

    exit(0)

def celeryWorker():
    #  start up celery worker thread
    # app = current_app._get_current_object()
    cworker = worker.worker(app=app)

    logger.info("****  main thread broker mq %s ****" % config.broker)

    options = {
        'app': 'orchestrator',
        'broker': config.broker,
        'queues': 'testorchestrator',
        'queue.purge': 'testorchestrator',
        'purge': 'testorchestrator',
        'loglevel': 'DEBUG',
        'traceback': True,
        'concurrency': 1
    }

    logger.info("****  Starting celery worker thread   *****")
    cworker.run(**options)
    logger.info("****  Stopped celery worker thread   *****")
    exit(0)


def signal_handler_function(signum, frame):
    logger.info("****  Exiting SIGNAL %d ****" % signum)
    exit(0)


def main():
    logging.basicConfig(level=logging.INFO)

    signal.signal(signal.SIGTERM, signal_handler_function)
    signal.signal(signal.SIGINT, signal_handler_function)
    signal.signal(signal.SIGILL, signal_handler_function)
    signal.signal(signal.SIGHUP, signal_handler_function)

    t = threading.Thread(target=orchestrator.main)
    t.start()

    celeryWorker()

    logger.info("****  Exited celeryWorker Thread   *****")

    exit(0)


if __name__ == "__main__":
    logger.info("****  main ****")
    main()
    exit(0)

if "orchestrator" in __name__:
    logger.info("****  main thread start ****")
    main()
    exit(0)
