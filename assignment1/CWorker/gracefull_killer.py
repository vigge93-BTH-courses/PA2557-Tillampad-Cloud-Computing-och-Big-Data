import signal
from threading import Event
from typing import Callable


class GracefulKiller:
    """https://stackoverflow.com/a/31464349/2591014"""

    kill_now = False

    def __init__(self, callback: Callable):
        self.callback = callback
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        self.kill_now = True
        self.callback()
