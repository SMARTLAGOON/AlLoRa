import utime
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

    def write_serial(self, content:bytes):
        # Prepend the length of the content to the content itself
        length = len(content)
        length_bytes = length.to_bytes(4, 'big')  # Convert length to 4 bytes
        message = length_bytes + content
        print("Sending serial: ", len(message), " -> {}".format(message))
        self.uart.write(message)

    def read_serial(self):
        # Read the length of the content
        if self.uart.any() >= 4:
            length_bytes = self.uart.read(4)  # Read 4 bytes for the length
            length = int.from_bytes(length_bytes, 'big')  # Convert bytes to int
            if length > 255:
                length = 255
            # Now read the content
            print("Content length: ", length)
            content = self.uart.read(length)
            return content
        else:
            return None

    def client_API(self):
        print("Waiting for serial data...")
        try:
            received_data = self.read_serial()
            if received_data:
                if self.mode == "requester":
                    success = self.handle_requester_mode(received_data)
                elif self.mode == "source":
                    sucess = self.handle_source_mode(received_data)
                return success
            return False
        except Exception as e:
            #utime.sleep(0.1)
            print("Error reading serial: ", e)
            return False
        
    
    def handle_requester_mode(self, received_data):
        packet_from_rpi = Packet(self.connector.mesh_mode)
        check = packet_from_rpi.load(received_data)
        if self.debug:
            print("Received serial data: ", received_data, check)
        if check:
            response_packet = self.connector.send_and_wait_response(packet_from_rpi)
            if response_packet:
                if response_packet.get_command():
                    response = response_packet.get_content()
                    print("Sending serial: ", len(response), " -> {}".format(response))
                    self.write_serial(response)
                    return True
            else:
                if self.debug:
                    print("No response...")
                return False

    def handle_source_mode(self, received_data):
        packet_from_source = Packet(self.connector.mesh_mode)
        try:
            packet_from_source.load(received_data)
            success = self.send_packet(packet_from_source)
        except: 
            received_data = received_data.decode("utf-8")
            if received_data.startswith("Listen:"):
                self.listen_and_process(received_data)

    def send_packet(self, packet_from_source):
        success = self.connector.send(packet_from_source)
        if success:
            if self.debug:
                print("Packet sent successfully")
            self.write_serial(b'OK')
        return success

    def listen_and_process(self, received_data):
        focus_time = int(received_data.split(":")[1])
        if self.debug:
            print("Listening for: ", focus_time)
        packet = Packet(mesh_mode=self.connector.mesh_mode)
        data = self.connector.recv(focus_time)
        if data:
            if self.debug:
                print("Received data: ", data)
            try:
                packet.load(data)
                response = packet.get_content()
                print("Sending serial: ", len(response), " -> {}".format(response))
                self.write_serial(response)
                #self.uart.write(response)
            except Exception as e:
                if self.debug:
                    print("Error loading: ", data, " -> ", e)
                self.uart.write(b'Error')
        else:
            if self.debug:
                print("No data received")
            self.write_serial(b'No data')
            #self.uart.write(b'No data')
