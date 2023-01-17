from time import sleep, time

from m3LoRaCTP.m3LoRaCTP_Packet import Packet

try:
    from os import urandom
except:
    from uos import urandom

class m3LoRaCTP_Node:

    def __init__(self, connector):
        self.open_backup()
        self.connector = connector
        self.config_connector()

        self.LAST_IDS = list()              # IDs from my mesagges
        self.LAST_SEEN_IDS = list()         # IDs from others
        self.MAX_IDS_CACHED = 30            # Max number of IDs saved

    def open_backup(self):
        with open("LoRa.txt", "r") as f:
            lora_config = f.readlines()

        self.__name = lora_config[0].split("=")[1].strip()
        self.__DEBUG = lora_config[5].split("=")[1].strip() == "True"
        self.mesh_mode = lora_config[4].split("=")[1].strip() == "True"
        self.__chunk_size = int(lora_config[3].split("=")[1].strip())

        freq = int(lora_config[1].split("=")[1].strip())
        sf = int(lora_config[2].split("=")[1].strip())
        self.config_connector_dic = {"freq" : freq, "sf": sf}
        
        if self.__DEBUG:
            print(self.__name , freq, sf, self.__chunk_size, self.mesh_mode, self.__DEBUG)

    def config_connector(self):
        self.connector.config(frequency = self.config_connector_dic["freq"], 
                                sf = self.config_connector_dic["sf"], 
                                mesh_mode = self.mesh_mode, 
                                debug = self.__DEBUG)
        
        self.__MAC = self.connector.get_mac()[8:]
        print(self.__name, ":", self.__MAC)

    def get_mesh_mode(self):
        return self.mesh_mode

    def __is_for_me(self, packet: Packet):
        return packet.get_destination() == self.__MAC

    def generate_id(self):
        id = -1
        while (id in self.LAST_IDS) or (id == -1):
            id = int.from_bytes(urandom(2), 'little')
        self.LAST_IDS.append(id)
        self.LAST_IDS = self.LAST_IDS[-self.MAX_IDS_CACHED:]
        return id

    def check_id_list(self, id):
        if id not in self.LAST_SEEN_IDS:
            self.LAST_SEEN_IDS.append(id)
            self.LAST_SEEN_IDS = self.LAST_SEEN_IDS[-self.MAX_IDS_CACHED:]
            return True
        else:
            return False

    def send_lora(self, packet):
        return self.connector.send(packet)

    def send_request(self, packet: Packet) -> Packet:
        if self.mesh_mode:
            packet.set_id(self.generate_id())
            if self.debug_hops:
                packet.enable_debug_hops()

        if self.connector:
            response_packet = self.connector.send_and_wait_response(packet)
            return response_packet

    def send_response(self, response_packet: Packet, destination):
        if response_packet:
            if self.mesh_mode:
                response_packet.set_id(self.generate_id())

                if self.__DEBUG:
                    print("SENT FINAL RESPONSE", response_packet.get_content())

            response_packet.set_destination(destination)
            if self.connector:
                self.send_lora(response_packet)

    def change_sf(self, sf):
        self.connector.backup_sf()
        self.connector.set_sf(sf)

    def restore_sf(self):
        self.connector.restore_sf()
