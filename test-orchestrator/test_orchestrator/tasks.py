#!/usr/bin/env python3
from __future__ import absolute_import, unicode_literals

import logging
import test_common.celeryconfig as config

from celery import Celery
from subprocess import run
from subprocess import Popen, PIPE
from test_common.util import Util

logger = logging.getLogger(__name__)

app = Celery('tasks', broker=config.broker)
app.config_from_object('test_orchestrator.celeryconfig')
route_key = 'test.tasks.testorchestrator'
app.conf.task_routes = {route_key: {'queue': 'testorchestrator'}}

logging.basicConfig(level=logging.INFO)

logger.info("****  task thread broker mq %s ****" % config.broker)


class tasks:
    @app.task
    def startClientd():
        global p
        p = Popen(['/opt/trinity/clientd', '-r', '169.47.24.196'], shell=True, stdin=PIPE, bufsize=1, universal_newlines=True)

    @app.task
    def sendAction(x):
        logger.info("Arg => " + x)
        p.stdin.write(x)
        p.stdin.write('\n')
        # p.communicate(input=x)

    @app.task
    def start(program):
        logger.info("********  Start process %s" % program)
        Popen([program], shell=True, bufsize=1, universal_newlines=True)

    @app.task
    def stop(program):
        run([program])

    @app.task
    def endpointReply(action, command, status, msg):
        try:

            if status == 'Error':
                logger.info("*** Error:  Reply Sending task {0} {1} {2} {3} ***".format(action, command, status, msg))
                Util.gErrors.append(msg)
            else:
                logger.info("*** Success: Reply Sending task {0} {1} {2} {3} ***".format(action, command, status, msg))

            if action == 'Policy.SetResponse':
                Util.messageQueue.put('success')
            if action == 'Policy.SetFailed':
                Util.messageQueue.put('failed')

        except Exception as e:
            logger.error("***************   Error    ******** ")
            logger.error(e)

    @app.task
    def registerClient(type, queue, route, hostname, dev_key):
        try:
            logger.info("*** Client Registering =>  {0} {1} {2} {3} {4} ***".format(type, queue, route, hostname, dev_key))
            args = list()
            args.append(queue)
            args.append(hostname)
            args.append(dev_key)
            Util.gClients[route] = args
        except Exception as e:
            logger.error("***************   Error    ******** ")
            logger.error(e)

    @app.task
    def startTest(file, numClients, tier, gwTier, packageName, protocol, test_mode):
        try:
            # task has been depricated
            logger.info("Start test called {0} {1} {2} {3} {4} {5} {6}".format(file, numClients, tier, gwTier, packageName, protocol, test_mode))
        except Exception as e:
            logger.error("***************   Error    ******** ")
            logger.error(e)

    @app.task
    def stopTest():
        # task has been depricated
        logger.info("Stop test message called")

    @app.task
    def status(test_id, status):
        logger.info("Status message called")
