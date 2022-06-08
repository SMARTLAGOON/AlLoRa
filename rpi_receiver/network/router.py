import collections
import json
import select
import socket
import time
from random import randint

import utils
from network.Packet import Packet

LAST_IDS = collections.deque(maxlen=30)


def generate_id():
    global LAST_IDS

    id = -1
    while (id in LAST_IDS) or (id == -1):
        id = randint(0, 65535)

    LAST_IDS.appendleft(id)

    return id


def send_packet(packet: Packet, mesh_mode: bool) -> Packet:
    json_response = None
    retry = True
    max_retries = 1
    #print(packet.get_content())
    response_packet = Packet(mesh_mode) # = mesh_mode

    while max_retries > 0 and retry is True:
        try:
            s = socket.socket()
            s.setblocking(True)
            addr = socket.getaddrinfo(utils.RECEIVER_API_HOST, utils.RECEIVER_API_PORT)[0][-1]
            s.settimeout(utils.SOCKET_TIMEOUT)
            s.connect(addr)
            if mesh_mode:
                packet.set_id(generate_id())    #_part("ID", str(generate_id()))

            content_str = packet.get_dict()
            content = json.dumps({"packet": content_str})

            httpreq = 'POST {} HTTP/1.1\r\nHost: {}\r\nConnection: close\r\nAccept: */*\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\r\n{}'.format(
                "/send-packet", utils.RECEIVER_API_HOST, len(content), content).encode('utf-8')

            ready_to_read, ready_to_write, in_error = select.select([],
                                                                    [s],
                                                                    [],
                                                                    15)
            s.send(httpreq)
            ready_to_read, ready_to_write, in_error = select.select([s],
                                                                    [],
                                                                    [s],
                                                                    15)
            response = s.recv(utils.SOCKET_RECV_SIZE)

            retry = False
            try:
                extracted_response = response.decode('utf-8').split('\r\n\r\n')[1]
                json_response = json.loads(extracted_response)
                response_packet.load_dict(json_response['response_packet'])
            except Exception as e:
                #print("Error in load: ", e)
                pass    # It fails when response is empty

        except Exception as e:
            utils.logger_error.error("Allowed Exception (Network connection was interrupted by some reason, but will keep trying to reconnect): {}".format(e))
            time.sleep(utils.PACKET_RETRY_SLEEP)
            retry = True
        finally:
            max_retries -= 1

    return response_packet
