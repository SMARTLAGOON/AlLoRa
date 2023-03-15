import time
import ubinascii
import network

from AlLoRa.Packet import Packet
from AlLoRa.Connectors.Connector import Connector

# Requires PyLora_SX127x_extensions to be installed
# https://github.com/GRCDEV/PyLora_SX127x_extensions
from PyLora_SX127x_extensions.pyLora import pyLora

class SX127x_connector(Connector):

    def __init__(self): #max_timeout = 10
        super().__init__()

        wlan_sta = network.WLAN(network.STA_IF)
        wlan_sta.active(True)
        wlan_mac = wlan_sta.config('mac')
        self.MAC = ubinascii.hexlify(wlan_mac).decode()[-8:]
        wlan_sta.active(False)

    def config(self, name = "S", frequency = 868, sf=7, mesh_mode=False, debug=False,  min_timeout = 0.5, max_timeout = 6):  #max_timeout = 10
        super().config(name, frequency, sf, mesh_mode, debug, min_timeout, max_timeout)
        self.lora = pyLora(freq = self.frequency,
                            sf=self.sf, verbose= self.debug)
        self.lora.setblocking(False) 

    def set_sf(self, sf):
        if self.sf != sf:
            self.lora.sf(sf)
            self.sf = sf
            if self.debug:
                print("SF Changed to: ", self.sf)

    def get_rssi(self):
        return self.lora.get_rssi()

    def send(self, packet):
        if self.debug:
            print("SEND_PACKET() || packet: {}".format(packet.get_content()))
        if packet.get_length() <= Connector.MAX_LENGTH_MESSAGE:
            try:
                self.lora.setblocking(True)
                self.lora.send(packet.get_content())  # .encode()
                self.lora.setblocking(False)
                return True
            except:
                self.lora.setblocking(False)
                return False
        else:
            if self.debug:
                print("Error: Packet too big")
            return False

    def recv(self, focus_time=12):
        try:
            self.lora.settimeout(focus_time)
            data = self.lora.recv(Connector.MAX_LENGTH_MESSAGE)
            return data
        except:
            if self.debug:
                print("nothing received or error")