import socket

class TCPConnection:
    BUFFER_SIZE = 1024

    def __init__(self, host, port, onData, onClose):
        self.onData = onData
        self.onClose = onClose
        self.connection = self.__connect(host, port)

    def readData(self):
        while True:
            buffer = self.connection.recv(self.BUFFER_SIZE)
            if not buffer: 
                self.onClose()
                return
            self.onData(buffer)

    def close(self):
        self.connection.shutdown(0)

    def __connect(self, host, port):
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connection.settimeout(1000)
        connection.connect((host, port))
        return connection