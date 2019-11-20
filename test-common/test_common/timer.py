import logging
from threading import Timer

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)


class pTimer(object):
    def __init__(self, interval, maxTime, runImmediate, runOnce, function, *args, **kwargs):
        self._timer = None
        self.function = function
        self.interval = interval
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.max = maxTime
        self.timer = 0
        self.once = False
        self.runOnce = runOnce

        if runImmediate:
            self.first()
        else:
            self.start()

    def __del__(self):
        logger.info('Remove timer object')

    def _run(self):
        if not self.runOnce:
            self.is_running = False
            self.start()
            self.function(*self.args, **self.kwargs)
        else:
            self.is_running = False
            self.start()
            if not self.once:
                self.once = True
                self.function(*self.args, **self.kwargs)

    def first(self):
        if not self.is_running:
            self._timer = Timer(0, self._run)
            self._timer.start()
            self.is_running = True

    def start(self):
        if not self.is_running:
            if self.max:
                self.timer += self.interval
            if self.timer <= self.max:
                self._timer = Timer(self.interval, self._run)
                self._timer.start()
                self.is_running = True
            else:
                self.stop()

    def stop(self):
        self._timer.cancel()
        self.function()
        self.is_running = False
