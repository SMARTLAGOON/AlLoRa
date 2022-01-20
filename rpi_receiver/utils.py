import json
import socket
import time
import select

def send_command(command: str, buoy_mac_address):
    json_response = None
    retry = True
    while retry is True:
        try:
            s = socket.socket()
            s.setblocking(True)
            addr = socket.getaddrinfo('192.168.4.1', 80)[0][-1]
            print(addr)
            s.settimeout(10)
            s.connect(addr)


            content = json.dumps({"command": command,
                                  "buoy_mac_address": buoy_mac_address})

            httpreq = 'POST {} HTTP/1.1\r\nHost: 192.168.4.1\r\nConnection: close\r\nAccept: */*\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\r\n{}'.format(
                "/send-command", len(content), content).encode('utf-8')


            ready_to_read, ready_to_write, in_error = select.select([],
                                                                    [s],
                                                                    [],
                                                                    15)
            s.send(httpreq)
            ready_to_read, ready_to_write, in_error = select.select([s],
                                                                    [],
                                                                    [s],
                                                                    15)
            response = s.recv(10000)

            retry = False
            extracted_response = response.decode('utf-8').split('\r\n\r\n')[1]
            json_response = json.loads(extracted_response)
        except Exception as e:
            print(e)
            time.sleep(5)
            retry = True
    return json_response['command_response']

