import ujson
from network import ETH
import utime
import os
import socket
from UARTInterface import *
import uhashlib
import ubinascii
import select


class CampbellScientificCR1000XWebRequest(UARTInterfaceListener):


    URL_OUTPUT_5_MIN = ('/tables.html?command=DataQuery&mode=most-recent&format=json&uri=dl:Output5min&p1=24', 'Output5min')
    URL_OUTPUT_60_MIN = ('/tables.html?command=DataQuery&mode=most-recent&format=json&uri=dl:Output60min&p1=24', 'Output60min')
    URL_OUTPUT_BATTERY = ('/tables.html?command=DataQuery&mode=most-recent&format=json&uri=dl:OutputBattery&p1=24', 'OutputBattery')
    URL_OUTPUT_DAILY = ('/tables.html?command=DataQuery&mode=most-recent&format=json&uri=dl:OutputDaily&p1=24', 'OutputDaily')
    URL_OUTPUT_DIAG = ('/tables.html?command=DataQuery&mode=most-recent&format=json&uri=dl:OutputDiag&p1=24', 'OutputDiag')


    def __init__(self, host: str):
        self.__host = host
        self.__prepare()


    def __prepare(self):
        eth = ETH()
        eth.init()
        print("connecting...")
        print(eth.ifconfig(config=('192.168.4.1', '255.255.255.0', '0.0.0.0', '0.0.0.0')))
        while not eth.isconnected():
            utime.sleep(1)
            print(".", end='')


    def do_action(self, command: str, uart_interface: UARTInterface):
        super().do_action(command)
        print("command", command)
        if command == "GET":
            print("GET")
            data = self.__read_datasource()
            try:
                uart_interface.write(message=data)
            except UARTParallelWritingException as e:
                print(e)


    def __read_datasource(self) -> str:
        print("_read_datasource triggered")

        urls = [CampbellScientificCR1000XWebRequest.URL_OUTPUT_5_MIN,
                CampbellScientificCR1000XWebRequest.URL_OUTPUT_60_MIN,
                CampbellScientificCR1000XWebRequest.URL_OUTPUT_BATTERY,
                CampbellScientificCR1000XWebRequest.URL_OUTPUT_DAILY,
                CampbellScientificCR1000XWebRequest.URL_OUTPUT_DIAG]

        responses = b""

        socket.timeout(10)
        s = socket.socket()
        try:
            addr = socket.getaddrinfo(self.__host, 80)[0][-1]
            print("trying datalogger addr", addr)
            s.connect(addr)
            s.setblocking(0)
            print('socket connected')
            for aux_url in urls:
                # it is possible to attach additional HTTP headers in the line below, but note to always close with \r\n\r\n
                httpreq = 'GET ' + aux_url[0] + ' HTTP/1.1 \r\nHOST: '+ self.__host + '\r\nConnection: close\r\nAccept: application/json, text/javascript, */*; q=0.01\r\nAccept-Encoding: gzip, deflate\r\nAccept-Language: es-ES,en;q=0.9\r\nUser-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.79 Safari/537.36\r\n\r\n'
                print('http request: \n', httpreq)
                ready_write = select.select([], [s], [], 10)
                if ready_write[1]:
                    s.send(httpreq)

                raw_response = b''
                exit_counter = 10
                while True:
                    buffer = s.recv(4096)
                    if buffer is None or len(buffer) <= 0:
                        print("dry socket")
                        exit_counter -= 0.1
                    else:
                        exit_counter = 10
                        print("waiting socket")
                        raw_response += buffer
                        if buffer.endswith(b'\r\n\r\n'):
                            break
                    utime.sleep(0.1) #If not, socket may get hanged

                responses += raw_response
                '''
                #Extract JSON
                response_chunks = raw_response.split(b'\r\n')
                response = ''
                for c in response_chunks:
                    if len(c) > 50 or (len(c) < 50 and (b'}' or b']') in c): #50 because it is a number that an useful chunk of a response will never get as length except those which are end parts, such as ] or }, otherwise, just headers and shitty characters
                        response += c.decode('utf-8')

                print(aux_url, response)
                #FIXME A random JSON parsing error happens, maybe it could be good idea to move the JSON processing to Raspberry Pi, as there are more resources to tackle the problem rather than from micropython.
                responses[aux_url[1]] = response#ujson.loads(response)
                utime.sleep(1)
                '''
            #print(responses)
            str_response = responses.decode('utf-8')
            filename = str(ubinascii.hexlify(uhashlib.sha256(str_response).digest()))
            print(filename)
        except Exception as e:
            print(e)
        finally:
            print("closed socket")
            s.close()

        return str_response
