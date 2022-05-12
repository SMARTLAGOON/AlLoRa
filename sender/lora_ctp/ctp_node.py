import gc
import network
from network import LoRa
import socket
import binascii
from time import sleep, ticks_ms, sleep_ms
from uos import urandom
from lora_ctp.File import File



class Node:

    REQUEST_DATA_INFO = "request_data_info"
    CHUNK = "chunk-"

    #MERGE
    def __init__(self, sf, chunk_size, mesh = True, debug = False):
        gc.enable()
        self.__lora = LoRa(mode=LoRa.LORA, frequency=868000000, region=LoRa.EU868, sf = sf)
        self.__lora_socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
        self.__lora_socket.setblocking(False)

        self.__mesh = mesh

        self.__MAC = binascii.hexlify(network.LoRa().mac()).decode('utf-8')

        self.__chunk_size = chunk_size

        self.__DEBUG = debug

        self.__file = None

        self.__LAST_SENT_IDS = list()
        self.__LAST_IDS = list()


    #MERGE
    def __is_for_me(self, packet: Packet):
        return packet.get_destination() == self.__MAC:


    #MERGE
    def __forward(self, packet: Packet):
        try:
            if packet.get_part("ID") not in LAST_SENT_IDS:
                print("FORWARDED", packet.get_content())
                sleep(urandom(1)[0] % 5 + 1)
                self.__lora_socket.send(data)
                self.__LAST_SENT_IDS.append(packet.get_part("ID"))
                self.__LAST_SENT_IDS = self.__LAST_SENT_IDS[-5:]
            else:
                print("ALREADY_FORWARDED", self.__LAST_SENT_IDS)
        except KeyError as e:
            # If packet was corrupted along the way, won't read the COMMAND part
            print("JAMMING FORWARDING", e)


    #MERGE
    def stablish_connection(self):
        try_connect = True
        while try_connect:
            packet = self.__listen_receiver()
            if packet:
                if self.__is_for_me(packet=packet):
                    if packet.get_part("COMMAND") is Node.REQUEST_DATA_INFO):
                        try_connect = False
                        return True
                    else:
                        if self.DEBUG:
                            print("ERROR: Asked for other than data info {}".format(data))
                else:
                    self.__forward(packet=packet)
            gc.collect()


    '''
    This function ensures that a received message matches the criteria of any expected message.
    '''
    #MERGE
    def __listen_receiver(self):
        packet = Packet()
    	data = self.__lora_socket.recv(256)
        if not packet.load(data.decode('utf-8')):
            return None

    	if self.__DEBUG:
    		self.__rssi_calc()
    		print('LISTEN_RECEIVER() || received_content', packet.get_content())

        return packet


    '''
    This function prints the signal strength of the last received package over LoRa
    '''
    #MERGE
    def __rssi_calc(self):
        percentage = 0
    	rssi = self.__lora.stats()[1]
    	if (rssi >= -50):
    		percentage = 100
    	elif (rssi <= -50) and (rssi >= -100):
    		percentage = 2 * (rssi + 100)
    	elif (rssi < 100):
    		percentage = 0
    	print('SIGNAL STRENGTH', percentage, '%')


    #MERGE
    def send_file(self, name, content):
        self.__file = File(name, content, self.__chunk_size)
        del(content)
        gc.collect()
        self.__handle_command(packet=packet, type=Node.REQUEST_DATA_INFO)
        while not self.__file.sent:
            packet = self.__listen_receiver()
            if self.__is_for_me(packet=packet): #FIXME Asegurar el forward fuera del while
                command = packet.get_part('COMMAND')
                if command.startswith(Node.CHUNK)):     #if packet.get_part("COMMAND") is Node.REQUEST_DATA_INFO):
                    self.__handle_command(command=command, type=Node.CHUNK) #TODO Sacar a variable global los String de comandos
                elif command.startswith(Node.REQUEST_DATA_INFO)):
                    self.__handle_command(command=command, type=Node.REQUEST_DATA_INFO)
            else:
                self.__forward(packet=packet)
        del(self.__file)
        gc.collect()
        self.__file = None

    # MERGE (check)
    def __handle_command(self, command: command, type: str):
        response_packet = None
        if type == "request-data-info":    # handle for new file
            if self.__file.first_sent and not self.__file.last_sent:	# If some chunks are already sent...
                self.file.sent_ok()
                return True
            elif self.__file.metadata_sent:
                self.__file.retransmission += 1
                if self.__DEBUG:
                    print("asked again for data_info")
            else:
                self.__file.metadata_sent = True

            #response = self.metadata_new_file.format(self.MAC, self.file.get_length(), self.file.get_name()).encode()
            response_packet = Packet()
    		response_packet.set_part("LENGTH", self.__file.get_length())
    		response_packet.set_part("FILENAME", self.__file.get_name())

        elif type == "chunk-":
            requested_chunk = int(command.split('-')[1])
            #requested_chunk = int(self.command.decode('utf-8').split(";;;")[1].split(":::")[1].split('-')[1])
            if self.__DEBUG:
                print("RC: {}".format(requested_chunk))
            #response = self.chunk_format.format(self.MAC, self.file.get_chunk(requested_chunk)).encode()
            response_packet = Packet()
    		response_packet.set_part("CHUNK", self.__file.get_chunk(requested_chunk))

            if not self.__file.first_sent:
                self.__file.report_SST(True)	#Registering new file t0

        if response:
            if self.__mesh:
                response_packet.set_part("ID", str(generate_id()))
            	sleep(urandom(1)[0] % 5 + 1)
            	self.__lora_socket.send(response_packet.get_content().encode())
            	print("SENT FINAL RESPONSE", response_packet.get_content())
            else:
                self.__lora_socket.send(response_packet.get_content().encode())
            sleep(0.1)
            del(response_packet)
            gc.collect()

    # MERGE (Check)
    def generate_id(self):
    	global LAST_IDS
    	id = -1
    	while (id in LAST_IDS) or (id == -1):
    		id = urandom(1)[0] % 999 + 0
    	LAST_IDS.append(id)
    	LAST_IDS = LAST_IDS[-5:]
    	return id




###########################################################################
     def __2handle_command(self, type):
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
                    self.file.report_SST(True)	#Registering new file t0

            if response:
                self.lora_socket.send(response)
                del(response)
                gc.collect()
            sleep(0.1)

    def generate_id(self):
    	global LAST_IDS
    	id = -1
    	while (id in LAST_IDS) or (id == -1):
    		id = uos.urandom(1)[0] % 999 + 0
    	LAST_IDS.append(id)
    	LAST_IDS = LAST_IDS[-5:]
    	return id
    '''
    This function sends a response depending on which command was received
    '''
    def handle_command(command, type):
    	global socket
    	global DEBUG
    	global MAC
    	global log_file
    	global READ_NEW_LOG_FILE

    	response = None
    	if type == "request-data-info":
    		READ_NEW_LOG_FILE = True #It allows to load the next one
    		#response = "MAC:::{};;;LENGTH:::{};;;FILENAME:::{}".format(MAC.decode('utf-8'), log_file.get_length(), log_file.get_name()).encode()
    		response_packet = Packet()
    		response_packet.set_part("LENGTH", log_file.get_length())
    		response_packet.set_part("FILENAME", log_file.get_name())
    	elif type == "chunk-":
    		print("COMMAND", command)
    		requested_chunk = int(command.split('-')[1])
    		#response = "MAC:::{};;;CHUNK:::{}".format(MAC.decode('utf-8'), log_file.get_chunk(requested_chunk)).encode()
    		response_packet = Packet()
    		response_packet.set_part("CHUNK", log_file.get_chunk(requested_chunk))

    	response_packet.set_part("ID", str(generate_id()))
    	time.sleep(uos.urandom(1)[0] % 5 + 1)
    	socket.send(response_packet.get_content().encode())
    	print("SENT FINAL RESPONSE", response_packet.get_content())


    '''
    This function ensures that a received message matches the criteria of any expected message.
    '''

    def __listen_receiver():




    				if DEBUG == True:
    					print('LISTEN_RECEIVER() || received_content', packet.get_content())
    					print("my mac:", MAC.decode('utf-8'))
    				try:
    					if packet.get_part("ID") not in LAST_SENT_IDS:
    						command = packet.get_part('COMMAND')
    						if command.startswith('request-data-info'):
    							handle_command(command, "request-data-info") #TODO Sacar a variable global los String de comandos
    						elif command.startswith('chunk-'):
    							handle_command(command, "chunk-")
    						LAST_SENT_IDS.append(packet.get_part("ID"))
    						LAST_SENT_IDS = LAST_SENT_IDS[-5:]
    				except KeyError as e:
    					# If packet was corrupted along the way, won't read the COMMAND part
    					print("JAMMING RECEIVED", e)
