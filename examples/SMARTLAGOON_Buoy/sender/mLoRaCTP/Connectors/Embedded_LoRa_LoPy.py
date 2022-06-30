from time import sleep

from mLoRaCTP.mLoRaCTP_Packet import Packet
from mLoRaCTP.Connectors.Connector import Connector
from network import LoRa
import socket
import binascii

import pycom
import gc

class LoRa_LoPy_Connector(Connector):
    MAX_LENGTH_MESSAGE = 255

    def __init__(self, frequency=868000000, sf=7, mesh_mode=False, debug=False):

        super().__init__()
        self.__lora = LoRa(mode=LoRa.LORA, frequency=frequency,
                            region=LoRa.EU868, sf = sf)
        self.__lora_socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
        self.__lora_socket.setblocking(False)
        self.__MAC = binascii.hexlify(LoRa().mac()).decode('utf-8')

        self.__DEBUG = debug
        self.__mesh_mode = mesh_mode

        self.__WAIT_MAX_TIMEOUT = 10
        gc.enable()

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
            self.__lora_socket.send(packet.get_content())	#.encode()
            if packet.get_mesh():
                pycom.rgbled(0xb19cd8) # purple
            else:
                pycom.rgbled(0x007f00) # green
            sleep(0.1)
            pycom.rgbled(0)        # off
            del(packet)
            gc.collect()
            return True
        else:
            print("Error: Packet too big")
            return False

    def recv(self, size):
        data = self.__lora_socket.recv(size)
        return data

    def send_and_wait_response(self, packet):
        packet.set_source(self.get_mac())  # Adding mac address to packet

        self.lora.setblocking(True)
        success = self.send(packet)
        self.lora.setblocking(False)

        response_packet = Packet(self.__mesh_mode)  # = mesh_mode
        if success:
            timeout = self.__WAIT_MAX_TIMEOUT
            received = False
            received_data = b''
            while (timeout > 0 or received is True):
                if self.__DEBUG:
                    print("WAIT_RESPONSE() || quedan {} segundos timeout".format(timeout))
                try:
                    self.lora.settimeout(timeout)
                    received_data = self.recv(256)
                    if received_data:
                        if self.__DEBUG:
                            self.__signal_estimation()
                            print("WAIT_WAIT_RESPONSE() || sender_reply: {}".format(received_data))
                        # if received_data.startswith(b'S:::'):
                        try:
                            response_packet = Packet(self.__mesh_mode)  # = mesh_mode
                            response_packet.load(received_data)  # .decode('utf-8')
                            if response_packet.get_source() == packet.get_destination():
                                received = True
                                break
                            else:
                                response_packet = Packet(self.__mesh_mode)  # = mesh_mode
                        except Exception as e:
                            print("Corrupted packet received", e)
                except TimeoutError as e:
                    print("TimeOut!", e)
                timeout -= 1
        return response_packet
