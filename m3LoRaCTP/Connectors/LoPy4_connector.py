from time import sleep

from m3LoRaCTP.m3LoRaCTP_Packet import Packet
from m3LoRaCTP.Connectors.Connector import Connector
from network import LoRa
import socket
import binascii

import pycom
import gc

class LoPy4_connector(Connector):  

    def __init__(self):
        super().__init__()
        self.__MAC = binascii.hexlify(LoRa().mac()).decode('utf-8')
        gc.enable()

    def config(self, frequency = 868, sf=7, mesh_mode=False, debug=False, max_timeout = 6): #max_timeout = 100
        super().config(frequency, sf, mesh_mode, debug, max_timeout)
        self.__lora = LoRa(mode=LoRa.LORA, frequency=self.frequency*1000000,
                            region=LoRa.EU868, sf = self.sf)
        self.__lora_socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

    def set_sf(self, sf):
        if self.sf != sf:
            self.__lora.sf(sf)
            self.sf = sf
            if self.__DEBUG:
                print("SF Changed to: ", self.sf)

    def get_stats(self):
        stats = self.__lora.stats()
        if self.__DEBUG:
            print("rx_timestamp {0}, rssi {1}, snr {2}, sftx {3}, sfrx {4}, tx_trials {5}, tx_power {6}, tx_time_on_air {7}, tx_counter {8}, tx_frequency {9}".format(stats[0],
                    stats[1], stats[2], stats[3], stats[4], stats[5], stats[6], stats[7], stats[8], stats[9]))
        return stats

    def get_rssi(self):
        return self.__lora.stats()[1]
        
    def send(self, packet):
        if self.__DEBUG:
            print("SEND_PACKET() || packet: {}".format(packet.get_content()))
        if packet.get_length() <= Connector.MAX_LENGTH_MESSAGE:
            if packet.get_mesh():
                pycom.rgbled(0xb19cd8) # purple
            else:
                pycom.rgbled(0x007f00) # green
            try:
                self.__lora_socket.send(packet.get_content())	#.encode()
                #sleep(0.1)
                pycom.rgbled(0)        # off
                del(packet)
                gc.collect()
                return True
            except:
                pycom.rgbled(0)        # off
                return False
        else:
            if self.__DEBUG:
                print("Error: Packet too big")
            return False

    def recv(self, size=256):
        try:
            self.__lora_socket.settimeout(self.__WAIT_MAX_TIMEOUT)
            data = self.__lora_socket.recv(size)
            self.__lora_socket.setblocking(False)
            if self.__DEBUG:
                self.get_stats()
            return data
        except:
            if self.__DEBUG:
                print("nothing received or error")
