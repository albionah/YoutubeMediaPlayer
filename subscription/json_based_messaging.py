import json

class JsonBasedMessaging:
    def __init__(self, onMessage, onError):
        self.onMessage = onMessage
        self.onError = onError

    def onRawMessage(self, rawMessage):
        try:
            message = self.__parse(rawMessage)
            self.onMessage(message)
        except Exception as exception:
            print(rawMessage)
            self.onError(str(exception))

    def __parse(self, rawMessage):
        try:
            return json.loads(rawMessage)
        except ValueError:
            raise Exception("Message could not be parsed to JSON!")