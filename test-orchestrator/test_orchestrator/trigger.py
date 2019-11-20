#!/usr/bin/env python
import logging
import os
import signal
import sys
import test_common.celeryconfig as config
import threading
from time import sleep

from celery import Celery, current_app
from celery.bin import worker

from test_common.database import database
from test_common.util import Util

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

cworker = None
triggerThread = None

logger.info("****  main thread start {0} {1} ****".format(os.getpid(), os.getcwd()))

if len(sys.argv) < 6:
    logger.info("****  Usage: python3 trigger.py <remote task> <test name> <number of clients> <tier name> <GW tier name> <packages> <protocol> <repo> ****")  # noqa
    logger.info("****  Example: python3 trigger.py test_orchestrator.tasks.startTest test-cell.txt 10  test.v6.tsdn.io test.v6.tsdn.io udp  development****")  # noqa
    exit()


class trigger():
    def main():
        protocol = ''
        test_mode = 'download'
        maxTimeOut = 5 * 60  # add 5 minute timeout value
        timeOut = 0

        try:
            logging.basicConfig(level=logging.INFO)
            logger.info("****  trigger thread start %s ****" % os.getcwd())
            taskName = 'test_orchestrator.tasks.startTest'  # sys.argv[1]

            # ${TEST_NAME}.txt ${NUMBER_CLIENTS} ${TIER_NAME} ${GATEWAY} ${PACKAGES} ${PROTOCOL} ${TEST_MODE}

            testName = sys.argv[1]
            numberClients = sys.argv[2]
            tierName = sys.argv[3]

            if len(sys.argv) >= 5:
                gatewayName = sys.argv[4]

            if len(sys.argv) >= 6:
                packageList = sys.argv[5]

            if len(sys.argv) >= 7:
                protocol = sys.argv[6]

            if len(sys.argv) >= 8:
                test_mode = sys.argv[7]

            logger.info("Connecting to broker => " + config.broker)

            app = Celery('tasks', broker=config.broker)
            app.config_from_object('test_orchestrator.celeryconfig')

            route_key = 'test.tasks.testtrigger'
            app.conf.task_routes = {route_key: {'queue': 'testtrigger'}}

            logger.info("Sending test configuration to orchestrator {0} {1} {2} {3} {4} {5} {6} {7}".format(
                taskName, testName, numberClients, tierName, gatewayName, packageList, protocol, test_mode))

            # dequeue any old status messages
            CleanQueue()

            app.send_task(taskName, [testName, numberClients, tierName, gatewayName, packageList, protocol, test_mode],
                          queue='testorchestrator', routing_key='test.tasks.testorchestrator')

            logger.info("Sent test configuration...")

            while True:
                try:
                    logger.info("****  Waiting for Finished message   ****")
                    try:
                        test_id = ''
                        status = ''
                        test_id, status = Util.messageQueue.get(False)
                    except Exception as e:
                        logger.info("****  message queue Empty ****")
                        test_id = ''
                        status = ''

                    if status == 'done' or timeOut > maxTimeOut:
                        logger.info("****  Got message   {0} {1} ****".format(test_id, status))
                        db = database('testtier')
                        db.UpdateResults(test_id, test_mode)

                        Util.slackNotification(db, test_id, packageList)

                        workerExit(test_id)
                        exit(0)

                    sleep(2)
                    timeOut += 2
                except Exception as e:
                    logger.info("\n***************   Error *********\n")
                    logger.info(e)
        except Exception as e:
            logger.info("\n***************   Error *********\n")
            logger.info(e)


def CleanQueue():
    status = 'done'
    while 'done' in status:
        try:
            sleep(5)
            test_id, status = Util.messageQueue.get(False)
        except Exception as e:
            logger.info("****  message queue Empty ****")
            status = ''


def workerExit(test_id):
    Util.runCmd("echo " + test_id + " > testid")
    Util.runCmd("sudo pkill -f -TERM trigger")


def signal_handler_function(signum, frame):
    logger.info("****  Exiting SIGNAL %d ****" % signum)

    try:
        # cworker.app.control.broadcast('shutdown')
        # workerExit('')
        logger.info("****  sent shutdown ****")
        # cworker.app.control.shutdown()
    except Exception as e:
        logger.info(e)

    exit(0)


def celeryWorker():
    #  start up celery worker thread
    global cworker

    app = current_app._get_current_object()
    cworker = worker.worker(app=app)

    logger.info("****  main thread broker mq %s ****" % config.broker)

    options = {
        'app': 'trigger',
        'broker': config.broker,
        'queues': 'testtrigger',
        'queue.purge': 'testtrigger',
        'loglevel': 'DEBUG',
        'traceback': True,
        'concurrency': 1
    }

    logger.info("****  Starting celery worker thread   *****")
    cworker.run(**options)
    logger.info("****  Exiting celery worker thread   *****")
    triggerThread.do_run = False


logger.info("****  orchestrator **** " + __name__)

if __name__ == "__main__":
    logger.info("****  main ****")

    signal.signal(signal.SIGTERM, signal_handler_function)
    signal.signal(signal.SIGINT, signal_handler_function)
    signal.signal(signal.SIGILL, signal_handler_function)
    signal.signal(signal.SIGHUP, signal_handler_function)

    # start main thread if celery or watcher is main
    triggerThread = threading.Thread(target=trigger.main)
    triggerThread.start()

    celeryWorker()

    logger.info("****  Exiting trigger thread   *****")
    exit(0)

if "trigger" in __name__:
    logger.info("****  main trigger thread start ****")

    signal.signal(signal.SIGTERM, signal_handler_function)
    signal.signal(signal.SIGINT, signal_handler_function)
    signal.signal(signal.SIGILL, signal_handler_function)
    signal.signal(signal.SIGHUP, signal_handler_function)

    # start main thread if celery or watcher is main
    triggerThread = threading.Thread(target=trigger.main)
    triggerThread.start()

    celeryWorker()

    logger.info("****  Exiting trigger thread   *****")
    exit(0)
