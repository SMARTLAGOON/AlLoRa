import utime
from machine import UART
import struct
from AlLoRa.Packet import Packet
from AlLoRa.Interfaces.Interface import Interface
from AlLoRa.Connectors.Connector import Connector
from AlLoRa.utils.debug_utils import print

class Serial_Interface(Interface):

    def __init__(self):
        super().__init__()


    def setup(self, connector: Connector, debug, config):
        super().setup(connector, debug, config)
    
        if self.config_parameters:
            self.mode = self.config_parameters.get('mode', "requester")
            self.uartid = self.config_parameters.get('uartid', 1)
            self.baud = self.config_parameters.get('baud', 9600)
            self.tx = self.config_parameters.get('tx', None)
            self.rx = self.config_parameters.get('rx', None)
            self.bits = self.config_parameters.get('bits', 8)
            self.parity = self.config_parameters.get('parity', None)
            self.stop = self.config_parameters.get('stop', 1)

            self.uart = UART(self.uartid, self.baud)
            self.uart.init(baudrate=self.baud, tx=self.tx, rx=self.rx, 
                            bits=self.bits, parity=self.parity, stop=self.stop, 
                            timeout=800)
            if self.debug:
                print("Serial Interface configure: uartid: {}, baud: {}, tx: {}, rx: {}, bits: {}, parity: {}, stop: {}".format(self.uartid, 
                                                                                                                                self.baud, self.tx, self.rx, self.bits, self.parity, self.stop))
        utime.sleep(1)

    def listen_command(self, end_phrase=b"<<END>>\n"):
        buffer = bytearray()
        while True:
            if self.uart.any():
                buffer += self.uart.read(self.uart.any())
                if buffer.endswith(end_phrase):
                    return buffer[:-len(end_phrase)]
            else:
                utime.sleep(0.01)
        return None


    def client_API(self):
        command = self.listen_command()
        if command:
            if command.startswith(b"S&W:"):
                return self.handle_send_and_wait(command)
            elif command.startswith(b"Send:"):
                return self.handle_source_mode(command)
            elif command.startswith(b"Listen:"):
                return self.handle_requester_mode(command)
            else:
                return False
        else:
            return False

    def handle_send_and_wait(self, command):
        packet_from_rpi = Packet(self.connector.mesh_mode, self.connector.short_mac)
        data = command.split(b"S&W:")[-1]
        check = packet_from_rpi.load(data)
        # Send ACK:adaptive_timeout from connector
        if check:
            ack = b"ACK:" + str(self.connector.adaptive_timeout).encode() + b"<<END>>\n"
        else:
            ack = b"ACK:0<<END>>\n" # Error (0) in loading packet
        if self.debug:
            print("Sending ACK: ", ack)
        self.uart.write(ack)
        packet_from_rpi.replace_source(str(self.connector.get_mac()))
        response_packet, packet_size_sent, packet_size_received, time_pr = self.connector.send_and_wait_response(packet_from_rpi)
        if response_packet:
            if response_packet.get_command():
                response = response_packet.get_content() + b"<<END>>\n"
                if self.debug:
                    print("Sending serial: ", len(response), " -> {}".format(response))
                self.uart.write(response)
                return True
        else:
            if self.debug:
                print("No response...")
            return False
    
    def handle_source_mode(self, command):
        packet_from_source = Packet(self.connector.mesh_mode, self.connector.short_mac)
        # Send ACK to say that I will send it
        ack = b"OK"
        self.uart.write(ack)
        try:
            packet_from_source.load(command[5:])
            packet_from_source.set_source(self.connector.get_mac())
            success = self.connector.send(packet_from_source)
            if success:
                return True
        except Exception as e:
            if self.debug:
                print("Error loading packet: ", e)
            return False

    def handle_requester_mode(self, command):
        focus_time = int(command[7:])
        ack = b"OK"
        self.uart.write(ack)
        if self.debug:
            print("Listening for: ", focus_time)
        packet = Packet(mesh_mode=self.connector.mesh_mode, short_mac=self.connector.short_mac)
        data = self.connector.recv(focus_time)
        if data:
            if self.debug:
                print("Received data: ", data)
            try:
                packet.load(data)
                response = packet.get_content()
                response += b"<<END>>\n"
                if self.debug:
                    print("Sending serial: ", len(response), " -> {}".format(response))
                self.uart.write(response)
            except Exception as e:
                if self.debug:
                    print("Error loading: ", data, " -> ", e)
                self.uart.write(b'Error')
        else:
            if self.debug:
                print("No data received")
            self.uart.write(b'No data' + b"<<END>>\n")