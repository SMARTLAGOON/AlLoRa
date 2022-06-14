import socket
import binascii
import gc
from time import sleep, time

import pycom
from network import LoRa
from uos import urandom

from lora_ctp.File import File
from lora_ctp.Packet import Packet

class Node:

    REQUEST_DATA_INFO = "METADATA"  #"request-data-info"
    CHUNK = "CHUNK"                 #"chunk-"
    MAX_LENGTH_MESSAGE = 255    # Must check if packet <= this limit to send a message

    def __init__(self, name, sf, chunk_size = 235, mesh_mode = False, debug = False):
        gc.enable()
        self.__lora = LoRa(mode=LoRa.LORA, frequency=868000000, region=LoRa.EU868, sf = sf)
        self.__lora_socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
        self.__lora_socket.setblocking(False)

        self.__mesh_mode = mesh_mode
        self.__DEBUG = debug

        self.__name = name
        self.__MAC = binascii.hexlify(LoRa().mac()).decode('utf-8')[8:]
        #if self.__DEBUG:
        print(self.__name, " : ", self.__MAC)

        self.__chunk_size = chunk_size
        if self.__mesh_mode and self.__chunk_size > 233:   # Packet size less than 255 (with Spreading Factor 7)
            self.__chunk_size = 233 #183
            if self.__DEBUG:
                print("Chunk size force down to {}".format(self.__chunk_size))

        self.__file = None

        self.__LAST_SEEN_IDS = list()       # IDs that I forwarded
        self.__LAST_IDS = list()            # IDs from my mesagges
        self.__MAX_IDS_CACHED = 30
        pycom.rgbled(0x1aa7ec) # Picton Blue
        sleep(1)
        pycom.rgbled(0) # off

    #This function prints the aproximated signal strength of the last received package over LoRa
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

    # This function returns the RSSI of the last received packet
    def __raw_rssi(self):
        return self.__lora.stats()[1]

    def get_mesh_mode(self):
        return self.__mesh_mode

    def __is_for_me(self, packet: Packet):
        return packet.get_destination() == self.__MAC

    def got_file(self):     # Check if I have a file to send
        return self.__file is not None

    def stablish_connection(self):
        try_connect = True
        while try_connect:
            packet = self.__listen_receiver()
            if packet:
                if self.__is_for_me(packet):
                    command = packet.get_command()  #get_part('COMMAND')
                    destination = packet.get_source()
                    if command:
                        mesh_flag = False
                        if self.__mesh_mode and packet.get_mesh():    # To-Do enable/disable_mesh en load
                            mesh_flag = True
                        if command.startswith(Node.REQUEST_DATA_INFO):
                            pycom.rgbled(0x007f00) # green
                            try_connect = False
                            return True, None, mesh_flag, destination
                        elif command.startswith(Node.CHUNK):
                            pycom.rgbled(0x007f00) # green
                            try_connect = False
                            return True, self.__restore_backup(), mesh_flag, destination
                        else:
                            if self.__DEBUG:
                                print("ERROR: Asked for other than data info {}".format(packet.get_command()))  #part("COMMAND")
                else:
                    self.__forward(packet)
            gc.collect()

    #This function ensures that a received message matches the criteria of any expected message.
    def __listen_receiver(self):
        packet = Packet(mesh_mode = self.__mesh_mode)
        data = self.__lora_socket.recv(256)
        try:
            if not packet.load(data):   #.decode('utf-8')
                return None
        except Exception as e:
            if self.__DEBUG:
                print(e)
            return None

        if self.__mesh_mode:
            try:
                packet_id = packet.get_id() #Check if already forwarded or sent by myself
                if packet_id in self.__LAST_SEEN_IDS or packet_id in self.__LAST_IDS:
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
        try:
            if packet.get_mesh():
                if self.__DEBUG:
                    print("FORWARDED", packet.get_content())
                random_sleep = (urandom(1)[0] % 5 + 1) * 0.1
                if packet.get_debug_hops():
                    packet.add_hop(self.__name, self.__raw_rssi(), random_sleep)
                packet.enable_hop()
                pycom.rgbled(0x7f0000) # red
                sleep(random_sleep)  # Revisar
                pycom.rgbled(0)        # off

                if packet.get_length() <= Node.MAX_LENGTH_MESSAGE:
                    self.__lora_socket.send(packet.get_content())   #.encode()
                    self.__LAST_SEEN_IDS.append(packet.get_id())    #part("ID")
                    self.__LAST_SEEN_IDS = self.__LAST_SEEN_IDS[-self.__MAX_IDS_CACHED:]
                #else:
                #    if self.__DEBUG:
                #        print("ALREADY_FORWARDED", self.__LAST_SEEN_IDS)
        except Exception as e:
            # If packet was corrupted along the way, won't read the COMMAND part
            if self.__DEBUG:
                print("ERROR FORWARDING", e)

    def set_file(self, name, content):
        self.__file = File(name, content, self.__chunk_size)
        self.__backup_sending_file()
        del(content)
        gc.collect()

    def set_new_file(self, name, content, mesh_flag, destination):
        self.set_file(name, content)
        response_packet = self.__handle_command(command=Node.REQUEST_DATA_INFO)
        if self.__mesh_mode and mesh_flag and response_packet:
            response_packet.enable_mesh()
        self.__send(response_packet, destination)
        pycom.rgbled(0x007f00) # green
        sleep(0.1)
        pycom.rgbled(0)        # off
        del(response_packet)
        gc.collect()

    def restore_file(self, name, content):
        self.set_file(name, content)
        self.__file.first_sent = time()
        self.__file.metadata_sent = True

    def __send(self, response_packet: Packet, destination):
        if response_packet:
            if self.__mesh_mode:
                response_packet.set_id(self.__generate_id())    #part("ID", str(self.__generate_id()))
                t_sleep = 0
                if response_packet.get_debug_hops():
                    response_packet.add_hop(self.__name, self.__raw_rssi(), t_sleep)

                """
                if response_packet.get_mesh():  # == "1"  # To-Do enable/disable_mesh en load
                    t_sleep = (urandom(1)[0] % 10 + 1) * 0.1
                    pycom.rgbled(0xb19cd8) # purple
                    sleep(t_sleep)  # Revisar
                    pycom.rgbled(0)        # off
                """
                if self.__DEBUG:
            	       print("SENT FINAL RESPONSE", response_packet.get_content())
            #else:
                #response_packet.add_hop(self.__name, self.__raw_rssi(), 0)
                #response_packet.enable_hop()
            response_packet.set_destination(destination)
            if response_packet.get_length() <= Node.MAX_LENGTH_MESSAGE:
                self.__lora_socket.send(response_packet.get_content())  #.encode()
            else:
                print("Error: Packet too big")

    def send_file(self):
        while not self.__file.sent:
            mesh_flag = False
            destination = ''
            packet = self.__listen_receiver()
            if packet:
                if self.__is_for_me(packet=packet): #FIXME Asegurar el forward fuera del while
                    command = packet.get_command()  #_part('COMMAND')
                    destination = packet.get_source()
                    if command:
                        response_packet = None
                        if packet.get_debug_hops():
                            response_packet = Packet(mesh_mode = self.__mesh_mode)
                            response_packet.set_source(self.__MAC)
                            response_packet.set_data("")
                            response_packet.enable_debug_hops()
                        else:
                            if command.startswith(Node.CHUNK):     #if packet.get_part("COMMAND") is Node.REQUEST_DATA_INFO):
                                command = "{}-{}".format(Node.CHUNK, packet.get_payload().decode())
                                response_packet = self.__handle_command(command=command)
                            elif command.startswith(Node.REQUEST_DATA_INFO):
                                response_packet = self.__handle_command(command=command)
                        if response_packet:   # == "1"
                            if packet.get_mesh():
                                response_packet.enable_mesh()
                                mesh_flag = True

                        self.__send(response_packet, destination)
                        if response_packet:
                            if response_packet.get_mesh():
                                pycom.rgbled(0xb19cd8) # purple
                            else:
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
        return mesh_flag, destination

    def __handle_command(self, command: str):
        response_packet = None
        if command.startswith(Node.REQUEST_DATA_INFO):    # handle for new file
            if self.__file.first_sent and not self.__file.last_sent:	# If some chunks are already sent...
                self.__file.sent_ok()
                return None
            elif self.__file.metadata_sent:
                self.__file.retransmission += 1
                if self.__DEBUG:
                    print("asked again for data_info")
            else:
                self.__file.metadata_sent = True

            response_packet = Packet(self.__mesh_mode)   #mesh_mode =
            response_packet.set_source(self.__MAC)
            response_packet.set_metadata(self.__file.get_length(), self.__file.get_name())

        elif command.startswith(Node.CHUNK):
            requested_chunk = int(command.split('-')[1])
            #requested_chunk = int(self.command.decode('utf-8').split(";;;")[1].split(":::")[1].split('-')[1])
            if self.__DEBUG:
                print("RC: {}".format(requested_chunk))

            response_packet = Packet(mesh_mode = self.__mesh_mode)
            response_packet.set_source(self.__MAC)
            response_packet.set_data(self.__file.get_chunk(requested_chunk))

            if not self.__file.first_sent:
                self.__file.report_SST(True)	#Registering new file t0

        return response_packet

    def __generate_id(self):
        id = -1
        while (id in self.__LAST_IDS) or (id == -1):
            id = int.from_bytes(urandom(2), 'little')
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
