#!/usr/bin/env python3

import os
import socket
import fcntl
import struct
import multiprocessing
import logging
import array
import subprocess
import shlex
import json
import requests
import test_common.commands as TestCommands
import test_common.interface as interface

from datetime import datetime
from multiprocessing import Manager
from slackclient import SlackClient

counter_id = 0
api_key = os.environ['API_KEY']


logger = logging.getLogger(__name__)


class Util:
    manag = Manager()
    gClients = manag.dict()
    gErrors = manag.list()
    ixendpoints = dict()
    Clients = dict()
    messageQueue = multiprocessing.Queue()

    def get_ip_address():
        try:
            # return only first physical interface
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            for interface in Util.all_interfaces():
                if interface != 'lo':
                    return socket.inet_ntoa(fcntl.ioctl(
                        s.fileno(), 0x8915,  # SIOCGIFADDR
                        struct.pack(b'256s', interface[:15].encode())
                    )[20:24])
        except Exception as e:
            logger.error(e)

    def get_ip_addressByInterface(ifname):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            return socket.inet_ntoa(fcntl.ioctl(
                s.fileno(), 0x8915,  # SIOCGIFADDR
                struct.pack(b'256s', ifname[:15])
            )[20:24])
        except Exception as e:
            logger.error(e)

    def get_ip_address_byname(tier, hostname):
        try:
            ip = socket.gethostbyname(hostname)
            logger.info("Host Name IP '{0}'".format(ip))
            # for local testing
            if '127.0.0.1' in ip or '127.0.1.1' in ip:
                return ip

            hostname = '{0}.{1}'.format(hostname, tier)
            logger.info("Get Host by name '{0}'".format(hostname))
            return socket.gethostbyname(hostname)
        except Exception as e:
            logger.error(e)

    def getDeviceKey():
        return os.environ['DEVICE_KEY']

    def all_interfaces():
        max_possible = 128  # arbitrary. raise if needed.
        bytes = max_possible * 32
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        names = array.array('B', b'\0' * bytes)
        outbytes = struct.unpack('iL', fcntl.ioctl(
            s.fileno(),
            0x8912,  # SIOCGIFCONF
            struct.pack('iL', bytes, names.buffer_info()[0])
        ))[0]
        namestr = names.tostring()
        lst = list()
        for i in range(0, outbytes, 40):
            name = namestr[i:i+16].split(b'\0', 1)[0]
            lst.append(name.decode("utf-8"))
        return lst

    def readConfig(file):
        try:
            cList = list()
            testCommands = list()

            dirPath = os.path.dirname(os.path.realpath(__file__)).replace('test_common', 'test_orchestrator')
            file = '{0}/scripts/{1}.txt'.format(dirPath, file)

            logger.info("\n*******  Config  Test  %s ********\n" % file)

            with open(file) as f:
                for line in f:
                    logger.info("**  Line => " + line)
                    commands = shlex.split(line)

                    for command in commands:
                        cList.append(command.strip('\n'))

                    testCommands.append(cList)
                    cList = []

            for Commands in testCommands:
                for Command in Commands:
                    logger.info("** Config item => " + Command)
        except Exception as e:
            logger.error("\n***************   Error *********\n")
            logger.error(e)

        return testCommands

    def fileToJson(file):
        global counter_id
        counter_id += 1
        data = ''

        try:

            dirPath = os.path.dirname(os.path.realpath(__file__)).replace('test_common', 'test_orchestrator').replace('test-common', 'test-orchestrator')
            file = '{0}/traffic_control/{1}.json'.format(dirPath, file)

            logger.info("\n******* Read File  %s ********\n" % file)

            with open(file) as json_data:
                data = json.load(json_data)

                data["counter"] = str(counter_id)

        except Exception as e:
            logger.error("\n***************   Error *********\n")
            logger.error(e)

        return json.dumps(data)

    def getPackage(packageName, packageList):
        version = ''
        name = ''

        try:
            packageList = packageList.split(',')

            for package in packageList:
                if packageName in package:
                    packageInfo = package.split('_')
                    if len(packageInfo) > 1:
                        name = packageInfo[0]
                        version = packageInfo[1]

            if name == '':
                name = packageName
        except Exception as e:
            logger.error(e)

        return name, version

    def getPackages(packages):
        packageClient = ''
        packageGateway = ''

        try:
            if 'candidate' in packages:
                packageGateway = Util.getCanidateVersion('jumpnet-gateway')
                packageClient = Util.getCanidateVersion('jumpnet-client')
                packages = '{0},{1}'.format(packageGateway, packageClient)
            else:
                packageList = packages.split(',')

                for package in packageList:
                    if 'client' in package:
                        packageClient = package
                    if 'gateway' in package:
                        packageGateway = package
        except Exception as e:
            logger.error(e)

        return packageClient, packageGateway, packages

    def getCanidateVersion(package):
        version = ''

        try:
            candidates = Util.runCmdCollect(TestCommands.command_get_candidate_version.format(package))
            for candidate in candidates:
                packageList = candidate.split(':')
                if len(packageList) > 1:
                    version = '{package}_{version}'.format(package=package, version=packageList[1].strip())
        except Exception as e:
            logger.error(e)

        return version

    def checkClients(numberOfPariedEndpoints):
        ips = list()
        Util.Clients.clear()
        rc = False
        gateway = ''

        try:
            # So this will make sure we have all the endpoints registered
            # plus the gateway that is why there is minus one since the gateway takes a spot in the endpoint list
            if numberOfPariedEndpoints <= (len(Util.gClients)-1)/2:
                isEndpoint = 0
                for key, value in Util.gClients.items():
                    logger.info("** checkClients => %s %s %s %s" % (numberOfPariedEndpoints, key, value[0], value[1]))
                    args = list()

                    # now set the gateway. Kind of a hack but just something simple
                    #   to keep with how we were doing things before
                    if numberOfPariedEndpoints <= len(Util.Clients)/2:
                        isEndpoint = 2
                        args.append(isEndpoint)
                        args.append(value[0])
                        Util.Clients[key] = args
                        gateway = value[1]
                        logger.info("** Gateway => %d %s" % (len(ips), Util.Clients[key]))
                        break

                    if isEndpoint == 1:
                        args.append(isEndpoint)
                        args.append(value[0])
                        args.append(ips[(len(ips) - 1)])
                        args.append(value[2])
                        Util.Clients[key] = args
                        logger.info("** Clients => %s %s" % (key,  Util.Clients[key]))
                        isEndpoint = 0
                    else:
                        args.append(isEndpoint)
                        args.append(value[0])
                        Util.Clients[key] = args
                        isEndpoint = 1
                        sroute = key.split('.')
                        if len(sroute) > 2:
                            # get device key
                            dev_key = sroute[3]
                            args2 = list()
                            args2.append(dev_key)
                            args2.append(value[1])
                            ips.append(args2)
                            logger.info("** Servers => %d Server Args:%s  Client Pointer:%s" % (len(ips), args, args2))

                rc = True
            else:
                rc = False

        except Exception as e:
            logger.error("\n***************   Error *********\n")
            logger.error(e)

        return rc, gateway

    def runCmd(command):
        try:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
            process.wait()
        except Exception as e:
            logger.error(e)

    def runCmdCollect(command):
        collection = list()
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        while True:
            line = process.stdout.readline()
            if line != b'':
                collection.append(line.decode("utf-8"))
            else:
                break

        return collection

    def _seconds():
        return int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000)

    def slackNotification(db, encryption, test_id, commit_hash, branch_name):
        try:
            if db:
                results = db.query('perf_results', test_id)

                for result in results:
                    logger.info("Results: {0}".format(result))
                    if 'Success' in result.result:
                        message = '\n    '.join([
                            '*Perf Test Finished*',
                            'Status: {0}',
                            'Test ID: {1}',
                            'Packages: {2} {3}',
                            'Test Name: {4}',
                            'Number of Clients: {5}',
                            'Avg Mbps: {6}',
                            'Max Mbps: {7}',
                            'Percent Success: {8}%',
                            'Encryption: {9}',
                            'Commit Hash: {10}',
                            'Commit Ref: {11}'
                        ]).format(
                            result.result, test_id, result.gateway_version, result.client_version, result.test_name, result.num_clients,
                            result.avg_mbps, result.max_mbps, result.failed_rate, encryption, commit_hash, branch_name,
                        )
                    else:
                        message = '\n    '.join([
                            '*Perf Test Finished Failed*'
                            'Test ID: {0}',
                            'Test Name: {1}',
                            'Packages: {2} {3}',
                            'Commit Hash: {4}',
                            'Commit Ref: {5}',
                            'Reason: {6}',
                        ]).format(
                            test_id, result.test_name, result.gateway_version, result.client_version, commit_hash, branch_name, result.error_text)

            else:
                message = '\n    '.join([
                    '*Perf Test Finished Failed*',
                    'Test ID: {0}',
                    ' Reason: {1}',
                ]).format(
                    test_id, 'Failed to connect to database')

            sc = SlackClient('xoxp-10351633397-10359027170-438668796707-d20df1d259fd699fc08989342c15bdc4')
            sc.api_call("chat.postMessage", channel='CCW3B94GZ', text=message)
        except Exception as e:
            logger.info("\n***************   Error *********\n")
            logger.info(e)

    def _url(path):
        return 'https://dev-api.jsdn.io/v3' + path

    def update_status(key, state, source, info, results=None):
        resp = None

        try:

            payload = interface.RestAPI['update']['payload']
            status = interface.RestAPI['update']['payload']['status']

            status['state'] = state.lower()
            status['source'] = source
            status['message'] = info
            payload['api_key'] = api_key
            payload['key'] = key
            payload['status'] = status
            if results:
                payload['results'] = results

            url = Util._url(interface.RestAPI['update']['endpoint'] + key)

            msg = json.dumps(payload)

            resp = requests.put(url, json=msg)

            if resp.status_code!=200:
                logger.error("REST API Error {0}".format(resp))
                logger.error(" Url: {0}".format(url))
                logger.error(" Json: {0}".format(msg))

        except Exception as e:
            logger.info("\n***************   Error *********\n")
            logger.info(e)

        return resp

    def getTestConfig(key):
        resp = None
        commands = dict()
        config = dict()

        try:

            payload = interface.RestAPI['get']['payload']

            payload['api_key'] = api_key
            payload['key'] = key

            url = Util._url(interface.RestAPI['get']['endpoint'] + key)

            msg = json.dumps(payload)

            resp = requests.get(url, json=msg, headers={'Authorization': api_key })

            if resp.status_code!=200:
                logger.error("REST API Error {0}".format(resp))
                logger.error(" Url: {0}".format(url))
                logger.error(" Json: {0}".format(msg))

            obj = resp.json()

            test_config = obj.get('test_config')
            instructionSet = test_config.get('instruction_set').get('instructions')


            for instruction  in instructionSet:
              method = instruction.get('method')
              order = instruction.get('op_order')
              payload = instruction.get('payload')
              key = '{0}_{1}'.format(order,method)
              commands[key] = payload
  


            config['num_clients'] = test_config.get('num_clients')
            config['name'] = test_config.get('name')
            
            print("Test Num Clients:  {0}".format(config))  
            print("Test Instructions:  {0}".format(commands))           
        

        except Exception as e:
            logger.info("\n***************   Error *********\n")
            logger.info(e)

        return config, commands

    def getTestCommands(OpCommands):
        resp = None
        testCommands = list()
        arguments = list()
        packagelist = "" 
        sequence = 0 
        sortedOPCommands = sorted(OpCommands.items(), key=lambda x: int(x[0].split('_')[0]))
        
        logger.info("Command Table Entries: {0} {1} {2}".format(len(sortedOPCommands), len(TestCommands.command_table),TestCommands.command_table))

        for method, op  in sortedOPCommands:
            if not op:
                break;

            command = method.split('_')[1]
            payload = TestCommands.command_table["{0}_{1}".format(op,sequence)]

            logger.info("Method: {0} Payload: {1}".format(method,payload))

            arguments.append(command)

            if 'Install' in method: 
                arguments.append(payload['app'])    
                packagelist += "{0},".format(payload['package_list'])
            elif 'Sleep' in method:
                arguments.append(payload['duration'])

            elif 'JumpnetClient' in method:
                arguments.append(payload['endpoint'])

            elif 'SubflowEnable' in method:
                arguments.append(payload['interface_op'])
                arguments.append(payload['type'])

            elif 'UsageStats' in method:
                arguments.append(payload['endpoint'])
    
            elif 'PolicySet' in method:
                arguments.append(payload['policy'])
                arguments.append(payload['version'])
                arguments.append(payload['client'])
                arguments.append(payload['gw'])
                            
            elif 'TrafficControl' in method:
                arguments.append(payload['settings'])

            elif 'DeviceStatus' in method:
                arguments.append(payload['endpoint'])

            elif 'IperfServer' in method:
                # Nothing to do here yet
                pass
            elif 'IperfClient' in method:
                arguments.append(payload['duration'])

            elif 'Wait' in method:
                arguments.append('PolicyWait')

            elif 'Stop' in method:   
                # Nothing to do here yet 
                pass    
            elif 'Exit' in method:
                # Nothing to do here yet
                pass
            else:
                # log invalid op
                logger.error("Invalid OP Command for Instruction Set {0}".format(method))

            testCommands.append(arguments)
            arguments = []
            sequence += 1 

        return testCommands, packagelist


        
        
