import serial, struct
from time import sleep, time

from AlLoRa.Packet import Packet
from AlLoRa.Connectors.Connector import Connector
from AlLoRa.utils.debug_utils import print

class Serial_connector(Connector):
    MAX_ATTEMPTS = 30  # Maximum attempts before resetting
    RESET_TIMEOUT = 60  # Timeout in seconds before allowing another reset

    def __init__(self, reset_function=None):
        super().__init__()
        self.attempt_count = 0
        self.last_reset_time = 0
        self.reset_function = reset_function

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
            response = self.serial_receive(self.timeout)
            if response is None:  # Check if no response was received
                raise Exception("No ACK received")
            else:
                self.attempt_count = 0
            return response
        except Exception as e:
            if self.debug:
                print("Error sending command or no response: ", e)
            self.attempt_count += 1
            if self.debug:
                print("Attempt count: ", self.attempt_count, "/", self.MAX_ATTEMPTS) 

            if self.attempt_count >= self.MAX_ATTEMPTS:
                self.attempt_reset()
            else: # If the maximum attempts have not been reached
                if self.debug:
                    print("Max attempts not reached: ", self.attempt_count)

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

    def attempt_reset(self):
        if time() - self.last_reset_time > self.RESET_TIMEOUT:
            if self.reset_function is not None:
                if self.debug:
                    print("Resetting...")
                self.reset_function()  # Call the passed-in reset function
                self.attempt_count = 0
                self.last_reset_time = time()
            else:
                if self.debug:
                    print("No reset function provided.")
        else:
            if self.debug:
                print("Reset recently triggered, waiting...")

    def send_and_wait_response(self, packet: Packet):
        packet.set_source(self.get_mac())  # Adding mac address to packet
        command = b"S&W:" + packet.get_content() + b"<<END>>\n"  # Append the custom end phrase to the command
        packet_size_sent = len(packet.get_content())
        response = self.send_command(command)
        # Response should be ACK:adaptive_timeout
        if not response:
            return None, packet_size_sent, 0, 0

        if self.debug:
            print("ACK Response: ", response)

        try:
            if response.startswith(b"ACK:"):
                response = response.split(b"ACK:")[1]
                self.adaptive_timeout = float(response) + 0.5
                # Now wait for the actual response
                focus_time = self.adaptive_timeout

                t0 = time()
                received_data = self.serial_receive(focus_time)
                td = (time() - t0) / 1000  # Calculate the time difference in seconds
                packet_size_received = len(received_data) if received_data else 0

                if self.debug:
                    print("Received data: ", received_data)

                if received_data:
                    response_packet = Packet(self.mesh_mode, self.short_mac)
                    check = response_packet.load(received_data)
                    if check:
                        return response_packet, packet_size_sent, packet_size_received, td
                    else:
                        if self.debug:
                            print("Error loading packet")
                        return None, packet_size_sent, packet_size_received, td
                else:
                    if self.debug:
                        print("No data received")
                    return None, packet_size_sent, packet_size_received, td
            else:
                if self.debug:
                    print("No ACK received")
                return None, packet_size_sent, 0, 0
        except Exception as e:
            if self.debug:
                print("Error S&W: ", e)
            return None, packet_size_sent, 0, 0

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
    
