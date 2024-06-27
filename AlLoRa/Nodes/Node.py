try:
    from uos import urandom
    from ujson import loads, dumps
except:
    from os import urandom
    from json import loads, dumps

from AlLoRa.Packet import Packet
from AlLoRa.Connectors.Connector import Connector
    
class Node:

    def __init__(self, connector: Connector, config_file):
        self.config_file = config_file
        self.open_backup()
        self.connector = connector

        self.LAST_IDS = list()              # IDs from my mesagges
        self.LAST_SEEN_IDS = list()         # IDs from others
        self.MAX_IDS_CACHED = 30            # Max number of IDs saved

        self.sf_trial = None

        self.subscribers = []
        self.status = {}

        self.config_connector()

        self.status["Status"] = "WAIT"  # Status of the requester
        self.status["RSSI"] = "-" # Signal strength
        self.status["SNR"] = "-"  # Signal to Noise Ratio
        #self.status["SF"] = self.connector.sf

        self.status["Chunk"] = "-"  # Chunk being received
        self.status["File"] = "-"   # File name being received
        self.status["PSizeS"] = "-" # Packet Size Sent
        self.status["PSizeR"] = "-" # Packet Size Received
        self.status["Retransmission"] = 0   # Number of retransmissions
        self.status["TimePS"] = "-"    # Time to send packet
        self.status["TimePR"] = "-"    # Waiting time for response
        self.status["TimeBtw"] = "-"  # Time between reply
        self.status["CorruptedPackets"] = 0  # Number of corrupted packets


    def open_backup(self):
        with open(self.config_file, "r") as f:
            self.config = loads(f.read())

        self.name = self.config.get('name', "N")
        self.debug = self.config.get('debug', True)
        self.mesh_mode = self.config.get('mesh_mode', False)
        self.chunk_size = self.config.get('chunk_size', 235)

        self.config_connector_dic = self.config.get('connector', None)    #{"freq" : lora_config['freq'], "sf": lora_config['sf']}

        if self.debug:
            print(self.config)

    def backup_config(self):
        conf = {"name": self.name,
                "chunk_size": self.chunk_size,
                "mesh_mode": self.mesh_mode,
                "debug": self.debug,
                "connector" : self.connector.backup_config()}
        with open(self.config_file, "w") as f:
            f.write(dumps(conf))

    def config_connector(self):
        self.connector.config(self.config_connector_dic)
        self.connector.debug = self.debug

        self.MAC = self.connector.get_mac()[-8:]
        self.status["MAC"] = self.MAC
        print(self.name, ":", self.MAC)

    def get_mesh_mode(self):
        return self.mesh_mode

    def is_for_me(self, packet: Packet):
        return packet.get_destination() == self.MAC

    def generate_id(self):
        id = -1
        while (id in self.LAST_IDS) or (id == -1):
            id = int.from_bytes(urandom(2), 'little')
        self.LAST_IDS.append(id)
        self.LAST_IDS = self.LAST_IDS[-self.MAX_IDS_CACHED:]
        return id

    def check_id_list(self, id):
        if id in self.LAST_SEEN_IDS:
            return False
        self.LAST_SEEN_IDS.append(id)
        self.LAST_SEEN_IDS = self.LAST_SEEN_IDS[-self.MAX_IDS_CACHED:]
        return True

    def send_lora(self, packet):
        return self.connector.send(packet)

    def change_sf(self, sf):
        self.connector.backup_sf()
        self.connector.set_sf(sf)

    def restore_sf(self):
        self.connector.restore_sf()

    # Subscribers stuff:
    def register_subscriber(self, subscriber):
        if subscriber not in self.subscribers:
            self.subscribers.append(subscriber)

    def unregister_subscriber(self, subscriber):
        if subscriber in self.subscribers:
            self.subscribers.remove(subscriber)

    def notify_subscribers(self):
        for subscriber in self.subscribers:
            subscriber.update(self.status)
