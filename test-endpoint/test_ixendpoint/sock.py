#!/usr/bin/python3

import json
import logging
import socket
import subprocess
import test_common.interface as interface

from time import sleep

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)


class sock:
    def __init__(self, endpoint, dump=False):
        logger.info('Initialize socket...')
        self.client = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        try:
            self.endpoint = endpoint
            self.dump = dump
            self.SetFolderPermissions()

            if self.dump:
               logger.info('Create Dump socket endpoint...')
               self.client.bind(interface.dump_addr.format(endpoint))
            else:
               logger.info('Create Client side socket endpoint...')
               self.client.bind(interface.client_addr.format(endpoint))


            self.SetFilePermissions()

            # os.unlink(client_addr)
        except FileNotFoundError:
            pass

    def __del__(self):
        self.client.close()

    def SetFolderPermissions(self):
        logger.info('Setting permissions...')
        self.runCmd("sudo chown gitlab-runner:gitlab-runner /var/run/{0}".format(self.endpoint))
        if self.dump:
           self.runCmd("sudo rm {0}".format(interface.dump_addr.format(self.endpoint)))
        else:
           self.runCmd("sudo rm {0}".format(interface.client_addr.format(self.endpoint)))

    def SetFilePermissions(self):
        logger.info('Setting permissions...')
        if self.dump:
           self.runCmd("sudo chmod 777 {0}".format(interface.dump_addr.format(self.endpoint)))
        else:
           self.runCmd("sudo chmod 777 {0}".format(interface.server_addr.format(self.endpoint)))
           self.runCmd("sudo chmod 777 {0}".format(interface.client_addr.format(self.endpoint)))



    def SendWait(self, message):
        self.Send(message)
        self.waitResponse()

    def Send(self, message):
        try:
            logger.info("Send message {0}".format(message))
            self.client.sendto(message.encode(), interface.server_addr.format(self.endpoint))
        except Exception as e:
            logger.error('Error: Failed to send {0}'.format(e))

    def getMessage(self, messageType, payloadType, payload, maxRequest):
        response = False
        request = 0

        logger.info("get message {0}".format(messageType))

        message = self.buildMessage(messageType, payloadType, payload)

        while response is False and request < maxRequest:
           
            self.Send(message)
            message = self.waitResponse()
            response, data = self.handleMessage(message, messageType, payloadType)

            sleep(1)
            request += 1

        return response, data

    def buildMessage(self, messageType, payloadType='', payload=''):
        message = interface.messageTypes[messageType]
        if payloadType != '':
            message = message.format(payloadType)
        elif '{payload}' in message:
            message = message.format(payload=payload)
        return message

    def waitResponse(self):
        logger.info('Waiting for response...')
        data, server = self.client.recvfrom(16384)
        data = data.decode("utf-8")
        logger.info('Received from {0} : {1}'.format(server, data))

        return data

    def handleMessage(self, message, messageType, payloadType):
        try:
            logger.info("Handle message {0} {1}".format(message, messageType))

            if messageType == 'session':
                key = json.loads(message)["payload"]["key"]
                if key != '':
                    logger.info("Session Key ..{0}".format(key))
                    return True, key
            elif messageType == 'interface':
                addr4 = json.loads(message)["payload"][payloadType]["binding"]["address"]
                if addr4 != '':
                    logger.info("Interface ip..{0}".format(addr4))
                    return True, addr4
            elif messageType == 'UsageStats':
                return True, message
            elif messageType == 'UsageRaw':
                return True, message
            else:
                return True, message

        except Exception as e:
            err_no = 1
            err = "invalid json " + e
            logger.error("bad json")

        return False, ""

    def runCmd(self, command):
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        process.wait()
