import utime
import time
from machine import UART
import struct
from AlLoRa.Packet import Packet
from AlLoRa.Interfaces.Interface import Interface
from AlLoRa.Connectors.Connector import Connector

class Serial_Interface(Interface):

    def __init__(self):
        super().__init__()


    def setup(self, connector: Connector, debug, config):
        super().setup(connector, debug, config)

        if self.config_parameters:
            self.mode = self.config_parameters.get('mode', "listener")
            self.uartid = self.config_parameters.get('uartid', 1)
            self.baud = self.config_parameters.get('baud', 9600)
            self.tx = self.config_parameters.get('tx', None)
            self.rx = self.config_parameters.get('rx', None)
            self.bits = self.config_parameters.get('bits', 8)
            self.parity = self.config_parameters.get('parity', None)
            self.stop = self.config_parameters.get('stop', 1)

            self.uart = UART(self.uartid, self.baud)
            self.uart.init(baudrate=self.baud, tx=self.tx, rx=self.rx, bits=self.bits, parity=self.parity, stop=self.stop)
            if self.debug:
                print("Serial Interface configure: uartid: {}, baud: {}, tx: {}, rx: {}, bits: {}, parity: {}, stop: {}".format(self.uartid, 
                                                                                                                                self.baud, self.tx, self.rx, self.bits, self.parity, self.stop))
        utime.sleep(1)


    def client_API(self):
        while True:
            time.sleep(1)
            try:
                if self.uart.any():
                    received_data = self.uart.read(255)
                    packet_from_rpi = Packet(self.connector.mesh_mode)
                    check = packet_from_rpi.load(received_data)
                    if self.debug:
                        print("Received data: ", received_data, check)
                    if check:
                        response_packet = self.connector.send_and_wait_response(packet_from_rpi)
                        if response_packet:
                            if response_packet.get_command():
                                response = response_packet.get_content()
                                print("Sending serial: ", len(response), " -> {}".format(response))
                                self.uart.write(response_packet.get_content())
                        else:
                            if self.debug:
                                print("No response...")
				
            except Exception as e:
                   if self.debug:
                         print("Error: {}".format(e))

    # Wait for command from Node, if the length of the packet is 2, then it is a command
    # If the length is higher than 2, then it is a packet to be sent over LoRa
    def client_API_Sender(self):
        while True:
            time.sleep(1)
            try:
                if self.uart.any():
                    received_data = self.uart.read(255)
                    if self.debug:
                            print("Received data: ", received_data)
                    packet_from_sender = Packet(self.connector.mesh_mode)
                    check = packet_from_sender.load(received_data)  # Maybe meter en try/except
                    if check:
                            success = self.connector.send(packet_from_sender)
                            if success: # reply success by serial
                                if self.debug:
                                    print("Packet sent successfully")
                                self.uart.write(b'OK')

                    elif received_data.startswith("Listen:"):
                        focus_time = int(received_data.split(":")[1])
                        if self.debug:
                            print("Listening...")
                        packet = Packet(mesh_mode = self.connector.mesh_mode)
                        data = self.connector.recv(focus_time)
                        try:
                            if packet.load(data):
                                response = packet.get_content()
                                print("Sending serial: ", len(response), " -> {}".format(response))
                                self.uart.write(packet.get_content())
                        except Exception as e:
                            if self.debug:
                                print("Error loading: ", data, " -> ",e)
                            self.uart.write(b'Error')
                        
            except Exception as e:
                   if self.debug:
                         print("Error: {}".format(e))
