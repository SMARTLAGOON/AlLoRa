from AlLoRa.Packet import Packet

class Interface:

    def __init__(self):
        pass

    def setup(self, connector, debug, config):
        self.connector = connector
        self.debug = debug
        self.config_parameters = config

    def backup_config(self):
        return self.config_parameters

    def client_API(self):
        pass
