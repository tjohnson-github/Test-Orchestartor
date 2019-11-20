#!/usr/bin/env python3

import logging
import sys

from celery.events import EventReceiver
from kombu import Connection as BrokerConnection

import test_common.celeryconfig as config

logger = logging.getLogger(__name__)


class Monitor:
    def monitor():
        connection = BrokerConnection(config.broker)

        def on_event(event):
            logger.info("**** EVENT HAPPENED: %s" % event)

        def on_worker_disconnect(event):
            logger.info("******** Worker Disconnected: %s" % event)

        def on_worker_connect(event):
            logger.info("******** Worker Connected: %s" % event)

        def on_worker_heartbeat(event):
            # to do
            pass

        def on_task_failed(event):
            exception = event['exception']
            logger.info("TASK FAILED!", event, " EXCEPTION: ", exception)

        while True:
            try:
                with connection as conn:
                    recv = EventReceiver(conn, handlers={
                        'task-failed': on_task_failed,
                        'worker-online': on_worker_connect,
                        'worker-heartbeat': on_worker_heartbeat,
                        'worker-offline': on_worker_disconnect
                    })
                    recv.capture(limit=None, timeout=None, wakeup=True)
            except (KeyboardInterrupt, SystemExit):
                logger.info("EXCEPTION KEYBOARD INTERRUPT")
                sys.exit()
