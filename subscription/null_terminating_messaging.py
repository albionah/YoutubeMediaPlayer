
class NullTerminatingMessaging:
    MAX_MESSAGE_SIZE = 1 * 1024 * 1024
    TERMINATING_BYTE = bytes([0])

    def __init__(self, onSegment, onError):
        self.currentSegment = b""
        self.onSegment = onSegment
        self.onError = onError

    def onData(self, data):
        self.currentSegment += data
        if self.currentSegment.endswith(self.TERMINATING_BYTE):
            self.onSegment(self.currentSegment[:-len(self.TERMINATING_BYTE)].decode())
            self.currentSegment = b""
        elif len(self.currentSegment) > self.MAX_MESSAGE_SIZE:
            self.onError("Message reached maximum size limit!")
            self.currentSegment = b""