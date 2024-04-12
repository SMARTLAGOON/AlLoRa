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
            return self.serial_receive(self.timeout)
            
        except Exception as e:
            if self.debug:
                print("Error sending command: ", e)
            return None

    def serial_receive(self, focus_time, end_phrase=b"<<END>>\n"):
        start_time = time()
        full_message = bytearray()  # Use a bytearray to accumulate the message
        while True:
            if time() - start_time > focus_time:
                if self.debug:
                    print("Timeout waiting for response.")
                return None  # Return None to indicate a timeout occurred

            line = self.serial.readline()  # Read a line; returns bytes
            if line:
                full_message += line  # Append this line to the full message
                # Check if the end of this line signifies the end of the message
                if full_message.endswith(end_phrase):
                    # Remove the end phrase to return only the message content
                    return full_message[:-len(end_phrase)]
            else:
                sleep(0.01)  # Small delay to avoid hogging the CPU


    def send_and_wait_response(self, packet: Packet) -> Packet:
        packet.set_source(self.get_mac())  # Adding mac address to packet
        command = b"S&W:" + packet.get_content() + b"<<END>>\n"  # Append the custom end phrase to the command
        response = self.send_command(command)
        # Response should be ACK:adaptive_timeout
        if not response:
            return None
        if self.debug:
            print("ACK Response: ", response)
        try:
            if response.startswith(b"ACK:"):
                response = response.split(b"ACK:")[1]
                self.adaptive_timeout = float(response) + 0.5
                # Now wait for the actual response
                focus_time = self.adaptive_timeout
                received_data = self.serial_receive(focus_time)
                if self.debug:
                    print("Received data: ", received_data)
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
        command = b"Send:" + packet.get_content() + b"<<END>>\n"  # Append the custom end phrase to the command
        ack_response = self.send_command(command)  # Use send_command to transmit
        if ack_response and b"OK" in ack_response:  # Check if the response contains "OK"
            return True
        else:
            if self.debug:
                print("Send command not acknowledged or error occurred.")
            return False

    def recv(self, focus_time=12):
        command = b"Listen:" + str(focus_time).encode() + b"<<END>>\n"
        ack_response = self.send_command(command)
        if ack_response and b"OK" in ack_response:
            # Wait for the actual response
            received_data = self.serial_receive(focus_time)
            if received_data:
                if self.debug:
                    print("Received data: ", received_data)
                return received_data
            else:
                if self.debug:
                    print("No data received")
        else:
            if self.debug:
                print("Listen command not acknowledged or error occurred.")
        return None
    
