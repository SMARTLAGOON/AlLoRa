from time import sleep, time

from mLoRaCTP.mLoRaCTP_Packet import Packet

try:
    from os import urandom
except:
    from uos import urandom

class mLoRaCTP_Node:

    def __init__(self, mesh_mode = False, connector = None):

        self.mesh_mode = mesh_mode

        self.connector = connector
        if self.connector:
            self.connector.set_mesh_mode(self.mesh_mode)
            self.__MAC = self.connector.get_mac()[8:]

        self.LAST_IDS = list()              # IDs from my mesagges
        self.LAST_SEEN_IDS = list()         # IDs from others
        self.MAX_IDS_CACHED = 30            # Max number of IDs saved

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
                return self.connector.send(response_packet)
