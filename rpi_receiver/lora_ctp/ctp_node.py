import gc
from time import sleep, time
import socket
import binascii

from random import randint

from lora_ctp.Packet import Packet

class LoRA_CTP_Node:
    
    MAX_LENGTH_MESSAGE = 255    # Must check if packet <= this limit to send a message

    def __init__(self, mesh_mode = False, debug_hops = False, adapter = None):
        
        self.mesh_mode = mesh_mode

        self.adapter = adapter
        if self.adapter:
            self.adapter.set_mesh_mode(self.mesh_mode)
            self.__MAC = self.adapter.get_mac()[8:]
        else:
            from network import LoRa
            frequency = 868000000
            sf = 7
            self.__lora = LoRa(mode=LoRa.LORA, frequency=frequency,
                                region=LoRa.EU868, sf = sf)
            self.__lora_socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
            self.__lora_socket.setblocking(False)
            self.__MAC = binascii.hexlify(LoRa().mac()).decode('utf-8')[8:]
        
        self.LAST_IDS = list()
        self.LAST_SEEN_IDS = list()       # IDs from my mesagges
        self.MAX_IDS_CACHED = 30          # Max number of IDs saved
        
    def get_mesh_mode(self):
        return self.mesh_mode

    def generate_id(self):
        id = -1
        while (id in self.LAST_IDS) or (id == -1):
            id = randint(0, 65535)
        self.LAST_IDS.append(id)
        self.LAST_IDS = self.LAST_IDS[-self.MAX_IDS_CACHED:]
        return id

    def check_id_list(self, id):
        if id not in self.LAST_SEEN_IDS:
            self.LAST_SEEN_IDS.append(id)    #part("ID")
            self.LAST_SEEN_IDS = self.LAST_SEEN_IDS[-self.MAX_IDS_CACHED:]
            return True
        else:
            return False

    def send_request(self, packet: Packet) -> Packet:
        if self.mesh_mode:
            packet.set_id(self.generate_id())    #_part("ID", str(generate_id()))
            if self.debug_hops:
                packet.enable_debug_hops()
            
        if self.adapter:
            response_packet = self.adapter.send_and_wait_response(packet)
        else:
            pass # Other way to send data (lora_socket, dragino, etc)

        return response_packet

    # LoRa methods
    """ This function returns the RSSI of the last received packet"""
    def __raw_rssi(self):
        return self.__lora.stats()[1]

    def __signal_estimation(self):
        percentage = 0
        rssi = self.__raw_rssi()
        if (rssi >= -50):
            percentage = 100
        elif (rssi <= -50) and (rssi >= -100):
            percentage = 2 * (rssi + 100)
        elif (rssi < 100):
            percentage = 0
        print('SIGNAL STRENGTH', percentage, '%')

    '''This function send a LoRA-CTP Packet using raw LoRa'''
    def __send(self, packet):
        if self.__DEBUG:
            print("SEND_PACKET() || packet: {}".format(packet.get_content()))
        if packet.get_length() <= LoRA_CTP_Node.MAX_LENGTH_MESSAGE:
            #self.__lora_socket.send(packet.get_content())	#.encode()
            return True
        else:
            print("Error: Packet too big")
            return False

    def __recv(self):
        return self.__lora_socket.recv(256)
    
