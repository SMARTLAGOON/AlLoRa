import gc
import network
from network import LoRa
import socket
import binascii
from time import sleep, time
from uos import urandom
from lora_ctp.File import File
from lora_ctp.Packet import Packet
import pycom


class Node:

    REQUEST_DATA_INFO = "request-data-info"
    CHUNK = "chunk-"
    MAX_LENGTH_MESSAGE = 255    # Must check if packet <= this limit to send a message

    #MERGE
    def __init__(self, name, sf, chunk_size = 201, mesh = False, debug = False):
        gc.enable()
        self.__lora = LoRa(mode=LoRa.LORA, frequency=868000000, region=LoRa.EU868, sf = sf)
        self.__lora_socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
        self.__lora_socket.setblocking(False)

        self.__mesh = mesh
        self.__DEBUG = debug

        self.__name = name
        self.__MAC = binascii.hexlify(network.LoRa().mac()).decode('utf-8')[8:]
        #if self.__DEBUG:
        print(self.__MAC)

        self.__chunk_size = chunk_size
        if self.__mesh and self.__chunk_size > 183:   # Packet size less than 255 (with Spreading Factor 7)
            self.__chunk_size = 183
            if self.__DEBUG:
                print("Chunk size force down to {}".format(self.__chunk_size))

        self.__file = None

        self.__LAST_SEEN_IDS = list()
        self.__LAST_IDS = list()
        self.__MAX_IDS_CACHED = 30
        pycom.rgbled(0x1aa7ec) # Picton Blue
        sleep(1)
        pycom.rgbled(0) # off

    '''
    This function prints the aproximated signal strength of the last received package over LoRa
    '''
    def __signal_estimation(self):
        percentage = 0
    	rssi = self.__raw_rssi()
    	if (rssi >= -50):
    		percentage = 100
    	elif (rssi <= -50) and (rssi >= -100):
    		percentage = 2 * (rssi + 100)
    	elif (rssi < 100):
    		percentage = 0
    	print('SIGNAL STRENGTH', percentage, '%')

    """ This function returns the RSSI of the last received packet"""
    def __raw_rssi(self):
        return self.__lora.stats()[1]

    def __is_for_me(self, packet: Packet):
        return packet.get_destination() == self.__MAC

    def got_file(self):     # Check if I have a file to send
        return self.__file is not None

    def stablish_connection(self):
        try_connect = True
        while try_connect:
            packet = self.__listen_receiver()
            if packet:
                if self.__is_for_me(packet=packet):
                    command = packet.get_part('COMMAND')
                    mesh_flag = False
                    if self.__mesh and packet.get_mesh() == "1":    # To-Do enable/disable_mesh en load
                        mesh_flag = True
                    if command.startswith(Node.REQUEST_DATA_INFO):
                        pycom.rgbled(0x007f00) # green
                        try_connect = False
                        return True, None, mesh_flag
                    elif command.startswith(Node.CHUNK):
                        pycom.rgbled(0x007f00) # green
                        try_connect = False
                        return True, self.__restore_backup(), mesh_flag
                    else:
                        if self.__DEBUG:
                            print("ERROR: Asked for other than data info {}".format(packet.get_part("COMMAND")))
                else:
                    self.__forward(packet=packet)
            gc.collect()

    '''
    This function ensures that a received message matches the criteria of any expected message.
    '''
    def __listen_receiver(self):
        packet = Packet(mesh_mode = self.__mesh)
        data = self.__lora_socket.recv(256)

        try:
            if not packet.load(data.decode('utf-8')):
                return None
        except Exception as e:
            if self.__DEBUG:
                print(e)
            return None

        if self.__mesh:
            try:
                if packet.get_part("ID") in self.__LAST_SEEN_IDS:
                    if self.__DEBUG:
                        print("ALREADY_SEEN", self.__LAST_SEEN_IDS)
                    return None
            except Exception as e:
                print(e)

        if self.__DEBUG:
            self.__signal_estimation()
            print('LISTEN_RECEIVER() || received_content', packet.get_content())

        return packet


    def __forward(self, packet: Packet):
        try:    # Revisar si no lo envié yo mismo antes
            #if packet.get_part("ID") not in self.__LAST_SEEN_IDS:
            if packet.get_part("M") == "1":
                if self.__DEBUG:
                    print("FORWARDED", packet.get_content())
                random_sleep = (urandom(1)[0] % 5 + 1) * 0.1

                packet.add_hop(self.__name, self.__raw_rssi(), random_sleep)
                pycom.rgbled(0x7f0000) # red
                sleep(random_sleep)  # Revisar
                pycom.rgbled(0)        # off

                self.__lora_socket.send(packet.get_content().encode())
                self.__LAST_SEEN_IDS.append(packet.get_part("ID"))
                self.__LAST_SEEN_IDS = self.__LAST_SEEN_IDS[-self.__MAX_IDS_CACHED:]
                #else:
                #    if self.__DEBUG:
                #        print("ALREADY_FORWARDED", self.__LAST_SEEN_IDS)
        except KeyError as e:
            # If packet was corrupted along the way, won't read the COMMAND part
            if self.__DEBUG:
                print("JAMMING FORWARDING", e)

    def set_file(self, name, content):
        self.__file = File(name, content, self.__chunk_size)
        self.__backup_sending_file()
        del(content)
        gc.collect()

    def set_new_file(self, name, content, mesh_flag):
        self.set_file(name, content)
        response_packet = self.__handle_command(command=Node.REQUEST_DATA_INFO, type=Node.REQUEST_DATA_INFO)
        if self.__mesh and mesh_flag and response_packet:
            response_packet.enable_mesh()
        self.__send(response_packet)
        pycom.rgbled(0x007f00) # green
        sleep(0.1)
        pycom.rgbled(0)        # off
        del(response_packet)
        gc.collect()

    def restore_file(self, name, content):
        self.set_file(name, content)
        self.__file.first_sent = time()
        self.__file.metadata_sent = True

    def __send(self, response_packet: Packet):
        if response_packet:
            if self.__mesh:
                response_packet.set_part("ID", str(self.__generate_id()))
                t_sleep = 0
                if response_packet.get_mesh() == "1":    # To-Do enable/disable_mesh en load
                    t_sleep = (urandom(1)[0] % 10 + 1) * 0.1
                    pycom.rgbled(0xb19cd8) # purple
                    sleep(t_sleep)  # Revisar
                    pycom.rgbled(0)        # off
                #print(response_packet.get_content().encode())
                #print(len(response_packet.get_content().encode()))
                response_packet.add_hop(self.__name, self.__raw_rssi(), t_sleep)
            	#self.__lora_socket.send(response_packet.get_content().encode())
                if self.__DEBUG:
            	       print("SENT FINAL RESPONSE", response_packet.get_content())
            else:
                response_packet.add_hop(self.__name, self.__raw_rssi(), 0)
            self.__lora_socket.send(response_packet.get_content().encode())


    def send_file(self):
        while not self.__file.sent:
            mesh_flag = False
            packet = self.__listen_receiver()
            if packet:
                if self.__is_for_me(packet=packet): #FIXME Asegurar el forward fuera del while
                    command = packet.get_part('COMMAND')
                    response_packet = None
                    if command.startswith(Node.CHUNK):     #if packet.get_part("COMMAND") is Node.REQUEST_DATA_INFO):
                        response_packet = self.__handle_command(command=command, type=Node.CHUNK) #TODO Sacar a variable global los String de comandos
                    elif command.startswith(Node.REQUEST_DATA_INFO):
                        response_packet = self.__handle_command(command=command, type=Node.REQUEST_DATA_INFO)
                    if packet.get_mesh() == "1" and response_packet:
                        response_packet.enable_mesh()
                        mesh_flag = True
                    self.__send(response_packet)
                    if response_packet:
                        pycom.rgbled(0x007f00) # green
                        sleep(0.1)
                        pycom.rgbled(0)        # off
                        del(response_packet)
                        gc.collect()
                else:
                    self.__forward(packet=packet)

        del(self.__file)
        gc.collect()
        self.__file = None
        return mesh_flag


    def __handle_command(self, command: str, type: str):
        response_packet = None
        if type == Node.REQUEST_DATA_INFO:    # handle for new file
            if self.__file.first_sent and not self.__file.last_sent:	# If some chunks are already sent...
                self.__file.sent_ok()
                return None
            elif self.__file.metadata_sent:
                self.__file.retransmission += 1
                if self.__DEBUG:
                    print("asked again for data_info")
            else:
                self.__file.metadata_sent = True

            response_packet = Packet(mesh_mode = self.__mesh)
            response_packet.set_part("LENGTH", self.__file.get_length())
            response_packet.set_part("FILENAME", self.__file.get_name())

        elif type == Node.CHUNK:
            requested_chunk = int(command.split('-')[1])
            #requested_chunk = int(self.command.decode('utf-8').split(";;;")[1].split(":::")[1].split('-')[1])
            if self.__DEBUG:
                print("RC: {}".format(requested_chunk))
            #response = self.chunk_format.format(self.MAC, self.file.get_chunk(requested_chunk)).encode()
            response_packet = Packet(mesh_mode = self.__mesh)
            response_packet.set_part("CHUNK", self.__file.get_chunk(requested_chunk))

            if not self.__file.first_sent:
                self.__file.report_SST(True)	#Registering new file t0

        return response_packet


    def __generate_id(self):
    	id = -1
    	while (id in self.__LAST_IDS) or (id == -1):
    		id = urandom(1)[0] % 999 + 0
    	self.__LAST_IDS.append(id)
    	self.__LAST_IDS = self.__LAST_IDS[-self.__MAX_IDS_CACHED:]
    	return id

    def __clean_backup(self):
        backup = open('backup.txt', "wb")
        backup.write("")
        backup.close()

    def __backup_sending_file(self):
        backup = open('backup.txt', "wb")
        backup.write(self.__file.get_name())
        backup.close()

    def __restore_backup(self):
        backup = open('backup.txt', "rb")
        name = backup.readline().decode("utf-8")
        backup.close()
        return name
