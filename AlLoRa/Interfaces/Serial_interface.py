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
            self.uart.init(baudrate=self.baud, tx=self.tx, rx=self.rx, bits=self.bits, parity=self.parity, stop=self.stop)
            if self.debug:
                print("Serial Interface configure: uartid: {}, baud: {}, tx: {}, rx: {}, bits: {}, parity: {}, stop: {}".format(self.uartid, 
                                                                                                                                self.baud, self.tx, self.rx, self.bits, self.parity, self.stop))
        self.screen = None
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
        length_bytes = self.uart.read(4)  # Read 4 bytes for the length
        length = int.from_bytes(length_bytes, 'big')  # Convert bytes to int
        if length > 255:
            length = 255
        # Now read the content
        print("Content length: ", length)
        content = self.uart.read(length)
        return content

    def client_API(self):
        print("Waiting for serial data...")
        received_data = self.read_serial()
        print("Received serial: ", len(received_data), " -> {}".format(received_data))
        if self.mode == "requester":
            self.handle_requester_mode(received_data)
        elif self.mode == "source":
            self.handle_source_mode(received_data)
        utime.sleep(0.1)
    
    def handle_requester_mode(self, received_data):
        packet_from_rpi = Packet(self.connector.mesh_mode)
        check = packet_from_rpi.load(received_data)
        if self.debug:
            print("Received data: ", received_data, check)
            self.show_in_screen("Received", "data")
        if check:
            response_packet = self.connector.send_and_wait_response(packet_from_rpi)
            if response_packet:
                if response_packet.get_command():
                    response = response_packet.get_content()
                    print("Sending serial: ", len(response), " -> {}".format(response))
                    self.show_in_screen("Sending", "serial")
                    self.write_serial(response)
                    #self.uart.write(response_packet.get_content())
            else:
                if self.debug:
                    print("No response...")
                    self.show_in_screen("No", "response")

    def handle_source_mode(self, received_data):
        packet_from_source = Packet(self.connector.mesh_mode)
        try:
            packet_from_source.load(received_data)
            self.send_packet(packet_from_source)
        except: 
            received_data = received_data.decode("utf-8")
            if received_data.startswith("Listen:"):
                self.listen_and_process(received_data)

    def send_packet(self, packet_from_source):
        success = self.connector.send(packet_from_source)
        if success:
            if self.debug:
                print("Packet sent successfully")
                self.show_in_screen("Packet", "sent")
            self.write_serial(b'OK')
            #self.uart.write(b'OK')

    def listen_and_process(self, received_data):
        focus_time = int(received_data.split(":")[1])
        if self.debug:
            print("Listening...")
            self.show_in_screen("Listening", "...")
        packet = Packet(mesh_mode=self.connector.mesh_mode)
        data = self.connector.recv(focus_time)
        if data:
            if self.debug:
                print("Received data: ", data)
                self.show_in_screen("Received", "data")
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
                self.show_in_screen("Error", "loading packet")
        else:
            if self.debug:
                print("No data received")
                self.show_in_screen("No", "data")
            self.write_serial(b'No data')
            #self.uart.write(b'No data')

    def set_screen(self, screen):
        print("Setting screen")
        self.screen = screen
        self.show_in_screen("Serial", "Interface")

    def show_in_screen(self, text1, text2):
        if self.screen == None:
            return
        self.screen.fill(0)
        self.screen.fill_rect(0, 0, 32, 32, 1)
        self.screen.fill_rect(2, 2, 28, 28, 0)
        self.screen.vline(9, 8, 22, 1)
        self.screen.vline(16, 2, 22, 1)
        self.screen.vline(23, 8, 22, 1)
        self.screen.fill_rect(26, 24, 2, 4, 1)
        self.screen.text("AlLoRa", 40, 0, 1)
        self.screen.text(text1, 40, 12, 1)
        self.screen.text(text2, 40, 24, 1)
        self.screen.show()
