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

    def config(self, config_json):
        super().config(config_json)
        self.lora = pyLora(freq = self.frequency,
                            sf=self.sf, 
                            bw=self.bw,
                            cr=self.cr,
                            output_power=self.tx_power,
                            verbose= self.debug)
        self.lora.setblocking(False) 

    def get_rssi(self):
        return self.lora.get_rssi()

    def get_snr(self):
        return self.lora.get_snr()

    def send(self, packet):
        if self.debug:
            print("SEND_PACKET() || packet: {}".format(packet.get_content()))
        if packet.get_length() <= Connector.MAX_LENGTH_MESSAGE:
            try:
                self.lora.setblocking(True)
                self.lora.send(packet.get_content())  # .encode()
                self.lora.setblocking(False)
                return True
            except Exception as e:
                if self.debug:
                    print("Error sending packet: ", e)
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
    
    def set_rf_config(self, frequency, sf, bw, cr, tx_power):
        self.change_rf_config(frequency, sf, bw, cr, tx_power)

    def set_frequency(self, freq):
        if self.frequency != freq:
            self.lora.set_frequency(freq)
            self.frequency = freq
            if self.debug:
                print("Frequency Changed to: ", self.frequency, self.lora.get_frequency())

    def set_sf(self, sf):
        if self.sf != sf:
            self.lora.sf(sf)
            self.sf = sf
            if self.debug:
                print("SF Changed to: ", self.sf)

    def set_bw(self, bw):
        print("BW:", bw)
        if self.bw != bw:
            try:
                self.lora.set_bandwidth(bw)
                self.bw = bw
                if self.debug:
                    print("BW Changed to: ", self.bw)
            except Exception as e:
                if self.debug:
                    print("Error changing BW: ", e)
        else:
            if self.debug:
                print("BW not changed")

    def set_cr(self, cr):
        if self.cr != cr:
            self.lora.set_coding_rate(cr)
            self.cr = cr
            if self.debug:
                print("CR Changed to: ", self.cr)

    def set_transmission_power(self, desired_power):
        # Set the desired transmission power in dBm
        self.lora.set_transmission_power_dbm(desired_power)
        if self.debug:
            print("Output Power Changed to: ", desired_power, "dBm")