import threading
import time
from .tcp_connection import TCPConnection
from .null_terminating_messaging import NullTerminatingMessaging
from .json_based_messaging import JsonBasedMessaging

class Subscriber:
    def __init__(self, host, port, onMessage, onError, onClose, retryIntervalInSeconds = 10):
        self.host = host
        self.port = port
        self.onMessage = onMessage
        self.onError = onError
        self.onClose = onClose
        self.retryIntervalInSeconds = retryIntervalInSeconds
        self.isRunning = True
        self.connection = None
        #self.thread = None

    def async_start(self):
        thread = threading.Thread(target=self.start)
        thread.daemon = True
        thread.start()
        return thread

    def start(self):
        while self.isRunning:
            try:
                self.connection = self.__connect()
                self.subscribe(self.connection)
            except Exception as exception:
                self.onError(exception)
                self.onClose()
            if self.isRunning:
                time.sleep(self.retryIntervalInSeconds)
    
    def subscribe(self, connection):
        connection.readData()

    # not functional
    def async_stop(self):
        self.stop()
        if self.thread and not self.thread.ident == threading.currentThread().ident:
            threading.Thread.join(self.thread)

    def stop(self):
        self.isRunning = False
        self.connection.close()

    def __connect(self):
        jsonBasedMessaging = JsonBasedMessaging(self.onMessage, self.__onError)
        nullTerminatingMessaging = NullTerminatingMessaging(jsonBasedMessaging.onRawMessage, self.__onError)
        return TCPConnection(self.host, self.port, nullTerminatingMessaging.onData, self.onClose)

    def __onError(self, error):
        self.connection.close()
        self.onError(error)