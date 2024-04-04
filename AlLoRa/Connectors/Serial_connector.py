import serial, struct
from time import sleep, time

from AlLoRa.Packet import Packet
from AlLoRa.Connectors.Connector import Connector

class Serial_connector(Connector):

    def __init__(self):
        super().__init__()
        
    def config(self, config_json):  #max_timeout = 10
        # JSON Example:
        # {
        #     "name": "N",
        #     "mesh_mode": false,
        #     "debug": false,
        #     "min_timeout": 0.5,
        #     "max_timeout": 6
        #     "serial_port": "/dev/ttyAMA3",
        #     "baud": 9600,
        #     "timeout": 1
        # }
        super().config(config_json)
        if self.config_parameters:
            self.serial_port = self.config_parameters.get('serial_port', "/dev/ttyAMA3")
            self.baud = self.config_parameters.get('baud', 9600)
            self.timeout = self.config_parameters.get('timeout', 1)
            self.serial = serial.Serial(self.serial_port, self.baud, timeout=self.timeout)
            if self.debug:
                print("Serial Connector configure: serial_port: {}, baud: {}, timeout: {}".format(self.serial_port, self.baud, self.timeout))
    
    def send_command(self, command):
        # Send command and wait for response
        try:
            self.serial.write(command)
            # Wait for ack response
            response = self.serial.readline()
            sleep(0.1)
            return response
        except Exception as e:
            print("Error sending command: ", e)
            return None

    def serial_receive(self, focus_time):
        start_time = time()
        while True:
            if self.serial.in_waiting:  # Check if there is data in the buffer
                received_data = self.serial.readline()
                return received_data
            if time() - start_time > focus_time:
                print("Timeout waiting for response.")
                return None

    def send_and_wait_response(self, packet: Packet) -> Packet:
        packet.set_source(self.get_mac())  # Adding mac address to packet
        command = b"S&W:" + packet.get_content()
        response = self.send_command(command)
        # Response should be ACK:adaptive_timeout
        if not response:
            return None
        try:
            response = response.decode("utf-8")
            if response.startswith("ACK:"):
                response = response.split(":")[1]
                self.adaptive_timeout = float(response)
                # Now wait for the actual response
                focus_time = self.adaptive_timeout
                received_data = self.serial_receive(focus_time)
                if received_data:
                    response_packet = Packet(self.mesh_mode)
                    check = response_packet.load(received_data)
                    if check:
                        return response_packet
                    else:
                        if self.debug:
                            print("Error loading packet")
                else:
                    if self.debug:
                        print("No data received")
            else:
                if self.debug:
                    print("No ACK received")
        except Exception as e:
            if self.debug:
                print("Error S&W: ", e)

    def send(self, packet: Packet):
        packet.set_source(self.get_mac())  # Adding mac address to packet
        command = b"Send:" + packet.get_content()
        response = self.send_command(command)
        try:
            response = response.decode("utf-8")
            if response == "OK":
                return True
            else:
                return False
        except Exception as e:
            print("Error sending packet: ", e)
            return False

    def recv(self, focus_time=12):
        command = "Listen:{0}".format(focus_time)
        response = self.send_command(command.encode('utf-8'))
        try:
            response = response.decode("utf-8")
            if response == "OK":
                received_data = self.serial_receive(focus_time)
                return received_data
            else:
                return None
        except Exception as e:
            print("Error receiving data: ", e)
            return None