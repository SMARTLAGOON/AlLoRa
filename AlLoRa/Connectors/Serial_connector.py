import serial, struct
from time import sleep, time


from AlLoRa.Packet import Packet
from AlLoRa.Connectors.Connector import Connector

class Serial_connector(Connector):

    def __init__(self, serial_port = "/dev/ttyAMA3", baud = 9600, timeout = 1):
        super().__init__()
        self.SERIAL_PORT = serial_port
        self.BAUD_RATE = baud
        self.timeout = timeout
        self.serial = serial.Serial(self.SERIAL_PORT, self.BAUD_RATE, timeout=self.timeout)
        

    def send_and_wait_response(self, packet: Packet) -> Packet:
        if self.debug:
            print("send and wait")
        retry = True
        max_retries = 1
        response_packet = Packet(self.mesh_mode)
        while max_retries > 0 and retry:
            try:
                content = packet.get_content()
                if self.debug:
                    print("Sending: ", content) 
                
                self.serial.write(content)
                sleep(1)
                received_data = self.serial.read(255)
                
                if received_data:
                    response_packet = Packet(self.mesh_mode)
                    check = response_packet.load(received_data)   
                    if check:
                        if self.debug:
                            print("Receiving: ", response_packet.get_content())
                        retry = False
                
            except Exception as e:
                retry = True
                if self.debug:
                    print("Error S&W: ", e)
            finally:
                max_retries -= 1

        return response_packet
    
    # Communicate with Serial Adapter and wait for status response
    def send(self, packet: Packet):
        try:
            content = packet.get_content()
            if self.debug:
                print("Sending: ", content) 
            self.serial.write(content)
            sleep(1)
            status_report = self.serial.read(255)
            if self.debug:
                print("Status: ", status_report)
            return status_report
        except Exception as e:
            if self.debug:
                print("Error Serial Send: ", e)
            return None
        
    # Ask Serial Adapter to listen for a packet for a certain amount of time and then wait for the response
    def recv(self, focus_time=12):
        try:
            #focus_time=100
            # pack listen command and focus_time
            command = "Listen:{0}".format(focus_time)
            self.serial.write(command.encode('utf-8'))
            sleep(1)
            # wait for response or timeout (focus time)
            wait = focus_time - 1
            while wait > 0:
                if self.serial.in_waiting:
                    break
                sleep(1)
                wait -= 1
                
            received_data = self.serial.read(255)
            if self.debug:
                print("Received: ", received_data)
            return received_data
        except Exception as e:
            if self.debug:
                print("Error Serial Recv: ", e)
            return None

            

