#!/usr/bin/env python3
from __future__ import absolute_import, unicode_literals

import logging
import signal

from celery import Celery

import test_common.celeryconfig as config
from test_common.util import Util

logger = logging.getLogger(__name__)

app = Celery('tasks', broker=config.broker)
app.config_from_object('test_orchestrator.celeryconfig')
route_key = 'test.tasks.testtrigger'
app.conf.task_routes = {route_key: {'queue': 'testtrigger'}}

logging.basicConfig(level=logging.INFO)

logger.info("****  task thread broker mq %s ****" % config.broker)


class ctasks:
    @app.task
    def stopTest():
        try:
            Util.gstartTest.value = False
            Util.gnumClients.value = 0
        except Exception as e:
            logger.error("***************   Error    ******** ")
            logger.error(e)

    @app.task
    def status(test_id, status):
        try:
            logger.info("Status message called")
            Util.messageQueue.put([test_id, status])
        except Exception as e:
            logger.error("***************   Error    ******** ")
            logger.error(e)


def signal_handler_function(signum, frame):
    logger.info("****  Exiting SIGNAL %d ****" % signum)
    exit(0)


signal.signal(signal.SIGTERM, signal_handler_function)
signal.signal(signal.SIGINT, signal_handler_function)
signal.signal(signal.SIGILL, signal_handler_function)
signal.signal(signal.SIGHUP, signal_handler_function)
