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
        self.config_connector()

        self.LAST_IDS = list()              # IDs from my mesagges
        self.LAST_SEEN_IDS = list()         # IDs from others
        self.MAX_IDS_CACHED = 30            # Max number of IDs saved

        self.sf_trial = None


    def open_backup(self):
        with open(self.config_file, "r") as f:
            lora_config = loads(f.read())

        self.name = lora_config['name']
        self.debug = lora_config['debug']
        self.mesh_mode = lora_config['mesh_mode']
        self.chunk_size = lora_config['chunk_size']

        self.config_connector_dic = lora_config['connector']    #{"freq" : lora_config['freq'], "sf": lora_config['sf']}

        if self.debug:
            print(lora_config)

    def backup_config(self):
        conf = {"name": self.name,
                "chunk_size": self.chunk_size,
                "mesh_mode": self.mesh_mode,
                "debug": self.debug,
                "connector" : self.connector.backup_config()}
        with open(self.config_file, "w") as f:
            f.write(dumps(conf))

    def config_connector(self):
        self.connector.config(frequency = self.config_connector_dic["freq"],
                                sf = self.config_connector_dic["sf"],
                                mesh_mode = self.mesh_mode,
                                debug = self.debug,
                                min_timeout =  self.config_connector_dic["min_timeout"],
                                max_timeout = self.config_connector_dic["max_timeout"])

        self.MAC = self.connector.get_mac()[-8:]
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

    def send_request(self, packet: Packet) -> Packet:
        if self.mesh_mode:
            packet.set_id(self.generate_id())
            if self.debug_hops:
                packet.enable_debug_hops()

        response_packet = self.connector.send_and_wait_response(packet)
        return response_packet

    def send_response(self, response_packet: Packet):
        if response_packet:
            if self.mesh_mode:
                response_packet.set_id(self.generate_id())
            
            self.send_lora(response_packet)
            if self.debug:
                print("SENT:", response_packet.get_content())

    def change_sf(self, sf):
        self.connector.backup_sf()
        self.connector.set_sf(sf)

    def restore_sf(self):
        self.connector.restore_sf()
