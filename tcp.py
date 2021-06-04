import socket
import json
import threading


class TCP:
    BUFFER_SIZE = 1024
    MAX_MESSAGE_SIZE = 1 * 1024 * 1024
    TERMINATING_CHAR = ";"

    def __init__(self, host, port, on_message, on_close, on_error):
        self.on_message = on_message
        self.on_close = on_close
        self.on_error = on_error
        self.current_message = ""
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.connect((host, port))

    def start(self):
        self.thread = threading.Thread(target=self.read_data)
        self.thread.daemon = True
        self.thread.start()
        return self.thread

    def stop(self):
        self.connection.shutdown(0)
        if not self.thread.ident == threading.currentThread().ident:
            threading.Thread.join(self.thread)

    def read_data(self):
        while True:
            buffer = self.connection.recv(self.BUFFER_SIZE)
            if not buffer: 
                self.on_close()
                return
            self.current_message += buffer
            if self.current_message[-len(self.TERMINATING_CHAR):] == self.TERMINATING_CHAR:
                self.parse_current_message()
                self.current_message = ""
            elif len(self.current_message) > self.MAX_MESSAGE_SIZE:
                self.on_error(self, "Message reached maximum size limit!")
                self.current_message = ""

    def parse_current_message(self):
        try:
            json_message = json.loads(self.current_message[:-len(self.TERMINATING_CHAR)])
            self.on_message(self, json_message)
        except ValueError:
            print(self.current_message)
            self.on_error(self, "Message cannot be parsed to JSON!")





def on_message(tcp, error_message):
    print(error_message)

def on_error(tcp, error):
    print(error)
    tcp.stop()

def on_close():
    print("closed")

tcp = TCP("localhost", 12345, on_message, on_close, on_error)
t=tcp.start()
print("zde")
threading.Thread.join(t)
print("zde")