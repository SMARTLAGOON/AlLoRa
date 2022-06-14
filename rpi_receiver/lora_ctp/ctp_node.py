import socket
import binascii
import gc
from time import sleep, time

from random import randint
from time import strftime


from lora_ctp.Packet import Packet

class Node:

    def __init__(self, gateway = False, mesh_mode = False, debug_hops = False, adapter = None):
        self.__gateway = gateway
        self.__mesh_mode = mesh_mode
        self.__debug_hops = debug_hops

        self.adapter = adapter
        self.adapter.set_mesh_mode(self.__mesh_mode)
        
        self.__LAST_IDS = list()
        self.__LAST_SEEN_IDS = list()            # IDs from my mesagges
        self.__MAX_IDS_CACHED = 30          # Max number of IDs saved
        

    def get_mesh_mode(self):
        return self.__mesh_mode

    def set_adapter(self, SOCKET_TIMEOUT, RECEIVER_API_HOST, RECEIVER_API_PORT, 
                    SOCKET_RECV_SIZE, logger_error, PACKET_RETRY_SLEEP):
        
        self.SOCKET_TIMEOUT = SOCKET_TIMEOUT
        self.RECEIVER_API_HOST = RECEIVER_API_HOST
        self.RECEIVER_API_PORT = RECEIVER_API_PORT
        self.SOCKET_RECV_SIZE = SOCKET_RECV_SIZE
        self.logger_error = logger_error
        self.PACKET_RETRY_SLEEP = PACKET_RETRY_SLEEP
        self.adapter = True

    def __generate_id(self):
        id = -1
        while (id in self.__LAST_IDS) or (id == -1):
            id = randint(0, 65535)
        #self.LAST_IDS.appendleft(id)
        self.__LAST_IDS.append(id)
        self.__LAST_IDS = self.__LAST_IDS[-self.__MAX_IDS_CACHED:]
        return id

    def check_id_list(self, id):
        if id not in self.__LAST_SEEN_IDS:
            self.__LAST_SEEN_IDS.append(id)    #part("ID")
            self.__LAST_SEEN_IDS = self.__LAST_SEEN_IDS[-self.__MAX_IDS_CACHED:]
            return True
        else:
            return False

    def ask_metadata(self, mac_address, mesh):
        packet = Packet(self.__mesh_mode) 
        packet.set_destination(mac_address)
        packet.ask_metadata()    #set_part("COMMAND", "request-data-info")
        if mesh:
            packet.enable_mesh()
        response_packet = self.send_packet(packet)
        if self.save_hops(response_packet):
            return  (1, "hop_catch.json"), response_packet.get_hop()
        if response_packet.get_command() == "METADATA":
            try:
                metadata = response_packet.get_metadata()
                hop = response_packet.get_hop()
                length = metadata["LENGTH"]
                filename = metadata["FILENAME"]
                return (length, filename), hop
            except:
                return None, None
        else:
            return None, None

    def ask_data(self, mac_address, mesh, next_chunk):
        packet = Packet(self.__mesh_mode) 
        packet.set_destination(mac_address)
        packet.ask_data(next_chunk)
        if mesh:
            packet.enable_mesh()
        response_packet = self.send_packet(packet)
        if self.save_hops(response_packet):
            return b"0", response_packet.get_hop()
        if response_packet.get_command() == "DATA":
            try: 
                if self.__mesh_mode:
                    id = response_packet.get_id()
                    if not self.check_id_list(id):
                        return None, None
                chunk = response_packet.get_payload()
                hop = response_packet.get_hop()
                return chunk, hop

            except:
                return None, None
        else:
            return None, None

    def send_packet(self, packet: Packet) -> Packet:
        #print(packet.get_content())
        if self.__mesh_mode:
            packet.set_id(self.__generate_id())    #_part("ID", str(generate_id()))
            if self.__debug_hops:
                packet.enable_debug_hops()
            
        if self.adapter:
            response_packet = self.adapter.send(packet)
        else:
            pass # Other way to send data (lora_socket, dragino, etc)

        return response_packet

    def save_hops(self, packet):
        if packet.get_debug_hops():
            hops = packet.get_message_path()
            t = strftime("%Y-%m-%d_%H:%M:%S")
            line = "{}:{}\n".format(t, hops)
            with open('log_rssi.txt', 'a') as log:
                log.write(line)
                #print(line)
            return True
        return False