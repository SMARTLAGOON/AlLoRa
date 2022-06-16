import _thread
import ujson
from lora_ctp.File import File
import utime
import os
import socket
from DataSource import DataSource
from machine import UART


class CampbellScientificCR1000X(DataSource):


    def __init__(self, file_chunk_size: int, file_queue_size=25, sleep_between_readings=60):
        super().__init__(file_chunk_size, file_queue_size, sleep_between_readings)
        self.__uart = UART(1, 115000)


    def _prepare(self):
        self.__uart.init(115000, bits=8, parity=None, stop=1, pins=('P3','P4'))


    def _read_datasource(self) -> File:
        file = None

        try:
            self.__uart.write("GET<<<END>>>")
            # Wait for content
            while (self.__uart.any() <= 0):
                utime.sleep(0.1)
            # When content is available
            data = b""
            while (self.__uart.any() > 0):
                while True:
                    #print("read")
                    try:
                        raw = self.__uart.read(256)
                        try:
                            if "<<<END>>>" in raw:
                                break
                        except Exception as e:
                            pass
                        data += raw
                    except Exception as e:
                        pass
                    utime.sleep(0.01)

            #print("END", data)
            #print("TYPE", type(data))

            #print("decode", type(data.decode('utf-8')))
            json_response = ujson.loads(data.decode('utf-8'))
            #print("post decoded")
            filename = json_response['Output5min']['data'][0]['time']
            file = File(name='{}.json'.format(filename), content=json_response, chunk_size=super()._get_file_chunk_size())
        except Exception as e:
            print(e)
        return file
