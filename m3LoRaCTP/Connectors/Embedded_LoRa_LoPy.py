from time import sleep

from m3LoRaCTP.m3LoRaCTP_Packet import Packet
from m3LoRaCTP.Connectors.Connector import Connector
from network import LoRa
import socket
import binascii

import pycom
import gc

class LoRa_LoPy_Connector(Connector):
    MAX_LENGTH_MESSAGE = 255

    def __init__(self, mesh_mode=False, debug=False, max_timeout = 100):

        super().__init__()
        self.__lora = LoRa(mode=LoRa.LORA, frequency=self.frequency,
                            region=LoRa.EU868, sf = self.sf)
        self.__lora_socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
        #self.__lora_socket.setblocking(False)
        self.__MAC = binascii.hexlify(LoRa().mac()).decode('utf-8')

        self.__WAIT_MAX_TIMEOUT = max_timeout
        self.__DEBUG = debug
        self.mesh_mode = mesh_mode
        gc.enable()

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

    def __signal_estimation(self):
        percentage = 0
        rssi = self.get_rssi()
        if (rssi >= -50):
            percentage = 100
        elif (rssi <= -50) and (rssi >= -100):
            percentage = 2 * (rssi + 100)
        elif (rssi < 100):
            percentage = 0
        print('SIGNAL STRENGTH', percentage, '%')

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
                return False
        else:
            print("Error: Packet too big")
            return False

    def recv(self, size=256):
        try:
            #self.__lora_socket.settimeout(0.5)
            #self.__lora_socket.setblocking(True)
            self.__lora_socket.settimeout(6)
            data = self.__lora_socket.recv(size)
            self.__lora_socket.setblocking(False)
            if self.__DEBUG:
                self.get_stats()
            return data
        except:
            pass

    def send_and_wait_response(self, packet):
        packet.set_source(self.__MAC)		# Adding mac address to packet
        success = self.send(packet)
        response_packet = Packet(self.mesh_mode)
        if success:
            timeout = self.__WAIT_MAX_TIMEOUT
            received = False
            received_data = b''
            while(timeout > 0 or received is True):
                received_data = self.recv()
                if received_data:
                    if self.__DEBUG:
                        self.__signal_estimation()
                        print("WAIT_WAIT_RESPONSE() || sender_reply: {}".format(received_data))
                    #if received_data.startswith(b'S:::'):
                    try:
                        response_packet = Packet(self.mesh_mode)
                        response_packet.load(received_data)
                        if response_packet.get_source() == packet.get_destination():
                            received = True
                            break
                        else:
                            response_packet = Packet(self.mesh_mode)
                    except Exception as e:
                        print("Corrupted packet received", e, received_data)
                sleep(0.01)
                timeout -= 1
        return response_packet
