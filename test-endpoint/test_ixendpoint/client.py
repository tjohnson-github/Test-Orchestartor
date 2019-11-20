import logging
import os
import signal
import socket
import test_common.celeryconfig as config
import threading

from time import sleep
from celery import Celery
from celery.bin import worker
from test_common.util import Util
from test_ixendpoint.tasks import tasks

mapp = Celery('tasks', broker=config.broker)
mapp.config_from_object('test_ixendpoint.celeryconfig')
dev_key = Util.getDeviceKey()

route_key = 'test.tasks.testendpoint.' + dev_key
queue = 'testendpoint.' + dev_key
hostname = socket.gethostname()


logger = logging.getLogger(__name__)


class client():
    def main():
        try:
            logging.basicConfig(level=logging.INFO)
            logger.info("****  client thread start %s ****" % os.getcwd())
            logger.info("****  client IP %s ****" % Util.get_ip_address())
            logger.info("****  client Broker MQ %s ****" % config.broker)

            while True:
                logger.info("****  Send Registration message  {0} {1} {2} ****".format(queue, route_key, hostname))
                mapp.send_task('test_orchestrator.tasks.registerClient',
                               ('endpoint', queue, route_key, hostname, dev_key),
                               queue='testorchestrator', routing_key='test.tasks.testorchestrator')
                sleep(60 * 1)
        except Exception as e:
            logger.info("\n***************   Error *********\n")
            logger.info(e)

        exit(0)


logger.info("****  client **** " + __name__)


def signal_handler_function(signum, frame):
    logger.info("****  Exiting SIGNAL %d ****" % signum)
    Util.runCmd("sudo pkill -f -TERM test-endpoint")
    exit(0)


def main():
    signal.signal(signal.SIGTERM, signal_handler_function)
    signal.signal(signal.SIGINT, signal_handler_function)
    signal.signal(signal.SIGILL, signal_handler_function)
    signal.signal(signal.SIGHUP, signal_handler_function)

    t = threading.Thread(target=client.main)
    t.start()

    # app = current_app._get_current_object()

    cworker = worker.worker(app=mapp)

    logging.basicConfig(level=logging.INFO)

    logger.info("****  main Broker MQ {0} **** Queue {1}".format(config.broker, queue))

    options = {
        'app': 'client',
        'broker': config.broker,
        'queues': queue,
        'queue.purge': queue,
        'purge': queue,
        'loglevel': 'DEBUG',
        'traceback': True,
        'concurrency': 1
    }

    cworker.run(**options)

    exit(0)


if __name__ == "__main__":
    logger.info("****  main ****")
    main()
    exit(0)


if "client" in __name__:
    logger.info("****  main thread start ****")
    # start main thread if celery or watcher is main
    main()
    exit(0)
