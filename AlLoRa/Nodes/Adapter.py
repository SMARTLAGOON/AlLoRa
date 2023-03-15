import gc
from AlLoRa.Nodes.Node import Node, Packet, urandom, loads, dumps
from AlLoRa.File import CTP_File
from AlLoRa.Connectors.Connector import Connector
from AlLoRa.Interfaces.Interface import Interface
from time import sleep, time

class Adapter(Node):

    def __init__(self, connector: Connector, interface: Interface, config_file = "LoRa.json"):
        super().__init__(connector, config_file)
        gc.enable()
        self.sf_trial = None
        self.interface = interface
        self.config_interface()

    def config_interface(self):
        with open(self.config_file, "r") as f:
            lora_config = loads(f.read())
        config_interface = lora_config['interface']
        self.interface.setup(self.connector, self.debug, config_interface)

    def backup_config(self):
        conf = {"name": self.name,
                "chunk_size": self.chunk_size,
                "mesh_mode": self.mesh_mode,
                "debug": self.debug,
                "connector" : self.connector.backup_config(),
                "interface": self.interface.backup_config()}
        with open(self.config_file, "w") as f:
            f.write(dumps(conf))

    def run(self):
        THREAD_EXIT = False		#Thread exit flag
        while True:
            try:
                if THREAD_EXIT:
                    break
                self.interface.client_API()  # change name
                gc.collect()

            except KeyboardInterrupt as e:
                THREAD_EXIT = True
                print("THREAD_EXIT")
