import socket
import json
import select
from time import sleep, time

from lora_ctp.Packet import Packet

class WiFi_adapter:

    def __init__(self, SOCKET_TIMEOUT, RECEIVER_API_HOST, RECEIVER_API_PORT, 
                    SOCKET_RECV_SIZE, logger_error, PACKET_RETRY_SLEEP):
        self.SOCKET_TIMEOUT = SOCKET_TIMEOUT
        self.RECEIVER_API_HOST = RECEIVER_API_HOST
        self.RECEIVER_API_PORT = RECEIVER_API_PORT
        self.SOCKET_RECV_SIZE = SOCKET_RECV_SIZE
        self.logger_error = logger_error
        self.PACKET_RETRY_SLEEP = PACKET_RETRY_SLEEP

    def set_mesh_mode(self, mesh_mode=False):
        self.__mesh_mode = mesh_mode

    def send(self, packet: Packet) -> Packet:
        json_response = None
        retry = True
        max_retries = 1
        response_packet = Packet(self.__mesh_mode) # = mesh_mode
        while max_retries > 0 and retry:
            try:
                s = socket.socket()
                s.setblocking(True)
                addr = socket.getaddrinfo(self.RECEIVER_API_HOST, self.RECEIVER_API_PORT)[0][-1]
                s.settimeout(self.SOCKET_TIMEOUT)
                s.connect(addr)

                content_str = packet.get_dict()
                content = json.dumps({"packet": content_str})

                httpreq = 'POST {} HTTP/1.1\r\nHost: {}\r\nConnection: close\r\nAccept: */*\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\r\n{}'.format(
                    "/send-packet", self.RECEIVER_API_HOST, len(content), content).encode('utf-8')

                ready_to_read, ready_to_write, in_error = select.select([],
                                                                        [s],
                                                                        [],
                                                                        15)
                s.send(httpreq)
                ready_to_read, ready_to_write, in_error = select.select([s],
                                                                        [],
                                                                        [s],
                                                                        15)
                response = s.recv(self.SOCKET_RECV_SIZE)

                retry = False
                try:
                    extracted_response = response.decode('utf-8').split('\r\n\r\n')[1]
                    json_response = json.loads(extracted_response)
                    response_packet.load_dict(json_response['response_packet'])
                except Exception as e:
                    #print("Error in load: ", e)
                    pass    # It fails when response is empty

            except Exception as e:
                self.logger_error.error("Allowed Exception (Network connection was interrupted by some reason, but will keep trying to reconnect): {}".format(e))
                sleep(self.PACKET_RETRY_SLEEP)
                retry = True
            finally:
                max_retries -= 1

        return response_packet