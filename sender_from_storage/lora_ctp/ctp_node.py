#import time
import gc
import network
from network import LoRa
import socket
import binascii
import time

from lora_ctp.File import File

class Node:

    def __init__(self, sf, chunk_size, debug = False):
        gc.enable()
        self.lora = LoRa(mode=LoRa.LORA, frequency=868000000, region=LoRa.EU868, sf = sf)
        self.lora_socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
        self.lora_socket.setblocking(False)

        self.MAC = binascii.hexlify(network.LoRa().mac()).decode('utf-8')

        self.chunk_size = chunk_size

        self.DEBUG = debug

        self.request_data_info_command = "MAC:::{};;;COMMAND:::{}".format(self.MAC, 'request-data-info').encode()
    	self.chunk_command = "MAC:::{};;;COMMAND:::{}".format(self.MAC, 'chunk-').encode()

        self.metadata_new_file = "MAC:::{};;;LENGTH:::{};;;FILENAME:::{}"
        self.chunk_format = "MAC:::{};;;CHUNK:::{}"

        self.command = None

        self.file = None

    def rssi_calc(self):
        percentage = 0
    	rssi = self.lora.stats()[1]
    	if (rssi >= -50):
    		percentage = 100
    	elif (rssi <= -50) and (rssi >= -100):
    		percentage = 2 * (rssi + 100)
    	elif (rssi < 100):
    		percentage = 0
    	print('SIGNAL STRENGTH', percentage, '%')

    def send_file(self, name, content):
        self.file = File(name, content, self.chunk_size)
        self.handle_command("request-data-info")
        while not self.file.sent:
            data = self.listen_receiver()
            if data.startswith(self.request_data_info_command):
                self.command = data
                self.handle_command("request-data-info") #TODO Sacar a variable global los String de comandos
            elif data.startswith(self.chunk_command):
                self.command = data
                self.handle_command("chunk-")

        del(self.file)
        gc.collect()
        self.file = None

    def stablish_connection(self):
        try_connect = True
        while try_connect:
            data = self.listen_receiver()
            if data.startswith(self.request_data_info_command):
                try_connect = False
                return True
            gc.collect()
            time.sleep(0.1)

    def listen_receiver(self):
        data = self.lora_socket.recv(256)
    	if self.DEBUG:
    		self.rssi_calc()
    		print('LISTEN_RECEIVER() || received_content', data)
    		print("my mac:", self.MAC)

        return data


    def handle_command(self, type):
        response = None
    	if type == "request-data-info":    # handle for new file
            if self.file.first_sent and not self.file.last_sent:	# If some chunks are already sent...
                self.file.sent_ok()
                return True
            elif self.file.metadata_sent:
                self.file.retransmission += 1
                if self.DEBUG:
                    print("asked again for data_info")
            else:
                self.file.metadata_sent = True

    		#READ_NEW_LOG_FILE = True #It allows to load the next one
    		response = self.metadata_new_file.format(self.MAC, self.file.get_length(), self.file.get_name()).encode()

        elif type == "chunk-":
            requested_chunk = int(self.command.decode('utf-8').split(";;;")[1].split(":::")[1].split('-')[1])
            if self.DEBUG:
                print("RC: {}".format(requested_chunk))
            response = self.chunk_format.format(self.MAC, self.file.get_chunk(requested_chunk)).encode()
            if not self.file.first_sent:
                self.file.report_SST(True)	# Reading new file

        if response:
            self.lora_socket.send(response)
            del(response)
        gc.collect()
        time.sleep(0.1)
