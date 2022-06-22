import _thread
import ujson
from lora_ctp.ctp_file import CTP_File
import utime
import os
import socket
from DataSource import DataSource
from machine import UART
import uhashlib
import ubinascii


class CampbellScientificCR1000X(DataSource):


    def __init__(self, file_chunk_size: int, file_queue_size=25, sleep_between_readings=60):
        super().__init__(file_chunk_size, file_queue_size, sleep_between_readings)
        self.__uart = UART(1, 115000)


    def _prepare(self):
        self.__uart.init(115000, bits=8, parity=None, stop=1, pins=('P3','P4'))


    def _read_datasource(self) -> CTP_File:
        file = None
        exit_counter = 10
        try:
            print("GET")
            self.__uart.write("GET<<<END>>>")
            exit_counter = 10
            ended = False
            data = b""
            while exit_counter > 0:
                raw = self.__uart.read(256)
                if raw is None or len(raw) <= 0:
                    #print("dry pipe")
                    exit_counter -= 0.01
                else:
                    #print("new msg")
                    exit_counter = 10
                    data += raw
                    if b"<<<END>>>" in raw:
                        ended = True
                        break
                utime.sleep(0.01)
            print("read")
            data = data.decode('utf-8')
            #print(data)
            if ended is True and data[:len("<<<BEGIN>>>")] == "<<<BEGIN>>>":
                data = data[len("<<<BEGIN>>>"):-len("<<<END>>>")]
                #If there are two merged files, file is invalid
                if "<<<BEGIN>>>" or "<<<END>>>" not in data:
                    hash = str(ubinascii.hexlify(uhashlib.sha256(data).digest()))
                    print(hash)

                    # Extract timestamp
                    filename = data.split('"time":  ')[1][1:20]
                    file = CTP_File(name='{}'.format(filename), content=data, chunk_size=super()._get_file_chunk_size())
        except Exception as e:
            print(e)
        return file
