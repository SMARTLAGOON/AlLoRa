import gc
from mLoRaCTP.Nodes.Base_Node import mLoRaCTP_Node, Packet, urandom
from mLoRaCTP.mLoRaCTP_File import CTP_File
from time import sleep, time

class mLoRaCTP_Sender(mLoRaCTP_Node):

    def __init__(self, name, chunk_size = 235, mesh_mode = False, debug = False, connector = None):
        mLoRaCTP_Node.__init__(self, mesh_mode, connector = connector)
        gc.enable()
        self.__name = name
        self.__DEBUG = debug

        self.__chunk_size = chunk_size
        if self.mesh_mode and self.__chunk_size > 233:   # Packet size less than 255 (with Spreading Factor 7)
            self.__chunk_size = 233
            if self.__DEBUG:
                print("Chunk size force down to {}".format(self.__chunk_size))

        print(self.__MAC)

        self.__file = None

    def get_chunk_size(self):
        return self.__chunk_size

    def got_file(self):     # Check if I have a file to send
        return self.__file is not None

    def set_file(self, file):
        self.__file = file

    def restore_file(self, file):
        self.set_file(file)
        self.__file.first_sent = time()
        self.__file.metadata_sent = True

    #This function ensures that a received message matches the criteria of any expected message.
    def __listen_receiver(self):
        packet = Packet(mesh_mode = self.mesh_mode)
        data = self.connector.recv(256)
        try:
            if not packet.load(data):   #.decode('utf-8')
                return None
        except Exception as e:
            if self.__DEBUG:
                print(e)
            return None

        if self.mesh_mode:
            try:
                packet_id = packet.get_id() #Check if already forwarded or sent by myself
                if packet_id in self.LAST_SEEN_IDS or packet_id in self.LAST_IDS:
                    if self.__DEBUG:
                        print("ALREADY_SEEN", self.LAST_SEEN_IDS)
                    return None
            except Exception as e:
                print(e)

        if self.__DEBUG:
            self.__signal_estimation()
            print('LISTEN_RECEIVER() || received_content', packet.get_content())

        return packet

    def establish_connection(self):
        while True:
            packet = self.__listen_receiver()
            if packet:
                if self.__is_for_me(packet):
                    command = packet.get_command()
                    destination = packet.get_source()
                    if Packet.check_command(command):
                        if command == Packet.OK:
                            response_packet = Packet(self.mesh_mode)
                            response_packet.set_source(self.__MAC)
                            response_packet.set_ok()
                            if self.mesh_mode and packet.get_mesh():
                                response_packet.enable_mesh()
                            if packet.get_debug_hops():
                                response_packet.add_previous_hops(packet.get_message_path())
                                response_packet.add_hop(self.__name, self.connector.get_rssi(), 0)
                            #pycom.rgbled(0x007f00) # green
                            self.send_response(response_packet, destination)
                            #pycom.rgbled(0)        # off
                            return False
                        else:
                            return True
                else:
                    self.__forward(packet)
            gc.collect()

    def send_file(self):
        while not self.__file.sent:
            destination = ''
            packet = self.__listen_receiver()
            if packet:
                if self.__is_for_me(packet=packet): #FIXME Asegurar el forward fuera del while
                    command = packet.get_command()  #_part('COMMAND')
                    destination = packet.get_source()
                    if Packet.check_command(command):
                        response_packet = None
                        if packet.get_debug_hops():
                            response_packet = Packet(mesh_mode = self.mesh_mode)
                            response_packet.set_source(self.__MAC)
                            response_packet.set_data("")
                            response_packet.enable_debug_hops()
                        else:
                            if command == Packet.CHUNK:     #if packet.get_part("COMMAND") is Node.REQUEST_DATA_INFO):
                                command = "{}-{}".format(Packet.CHUNK, packet.get_payload().decode())
                                response_packet = self.__handle_command(command=command)
                            else:   # Metadata or OK
                                response_packet = self.__handle_command(command=command)
                        if response_packet:
                            if packet.get_mesh():
                                response_packet.enable_mesh()
                            if packet.get_debug_hops():
                                response_packet.add_previous_hops(packet.get_message_path())
                                response_packet.add_hop(self.__name, self.__raw_rssi(), 0)

                        self.send_response(response_packet, destination)
                else:
                    self.__forward(packet=packet)

        del(self.__file)
        gc.collect()
        self.__file = None

    def __handle_command(self, command: str):
        response_packet = None
        if command.startswith(Packet.OK):
            if self.__file.first_sent and not self.__file.last_sent:	# If some chunks are already sent...
                self.__file.sent_ok()
                return None
            response_packet = Packet(self.mesh_mode)   #mesh_mode =
            response_packet.set_source(self.__MAC)
            response_packet.set_ok()

        if command.startswith(Packet.METADATA):    # handle for new file
            if self.__file.metadata_sent:
                self.__file.retransmission += 1
                if self.__DEBUG:
                    print("asked again for data_info")
            else:
                self.__file.metadata_sent = True

            response_packet = Packet(self.mesh_mode)   #mesh_mode =
            response_packet.set_source(self.__MAC)
            response_packet.set_metadata(self.__file.get_length(), self.__file.get_name())

        elif command.startswith(Packet.CHUNK):
            requested_chunk = int(command.split('-')[1])
            #requested_chunk = int(self.command.decode('utf-8').split(";;;")[1].split(":::")[1].split('-')[1])
            if self.__DEBUG:
                print("RC: {}".format(requested_chunk))

            response_packet = Packet(mesh_mode = self.mesh_mode)
            response_packet.set_source(self.__MAC)
            response_packet.set_data(self.__file.get_chunk(requested_chunk))

            if not self.__file.first_sent:
                self.__file.report_SST(True)	#Registering new file t0

        return response_packet

    def __forward(self, packet: Packet):
        try:
            if packet.get_mesh():
                if self.__DEBUG:
                    print("FORWARDED", packet.get_content())
                random_sleep = (urandom(1)[0] % 5 + 1) * 0.1
                if packet.get_debug_hops():
                    packet.add_hop(self.__name, self.__raw_rssi(), random_sleep)
                packet.enable_hop()
                sleep(random_sleep)  # Revisar


                success = self.__send(packet)
                if success:
                    self.LAST_SEEN_IDS.append(packet.get_id())    #part("ID")
                    self.LAST_SEEN_IDS = self.LAST_SEEN_IDS[-self.MAX_IDS_CACHED:]
                #else:
                #    if self.__DEBUG:
                #        print("ALREADY_FORWARDED", self.__LAST_SEEN_IDS)
        except Exception as e:
            # If packet was corrupted along the way, won't read the COMMAND part
            if self.__DEBUG:
                print("ERROR FORWARDING", e)
