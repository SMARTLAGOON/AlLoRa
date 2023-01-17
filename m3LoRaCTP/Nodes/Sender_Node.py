import gc
from m3LoRaCTP.Nodes.Base_Node import m3LoRaCTP_Node, Packet, urandom
from m3LoRaCTP.m3LoRaCTP_File import CTP_File
from time import sleep, time

class m3LoRaCTP_Sender(m3LoRaCTP_Node):

    def __init__(self, connector):
        super().__init__(connector)
        gc.enable()

        self.sf_trial = False
        
        if self.mesh_mode and self.__chunk_size > 233:   # Packet size less than 255 (with Spreading Factor 7)
            self.__chunk_size = 233
            if self.__DEBUG:
                print("Chunk size force down to {}".format(self.__chunk_size))

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

    def backup_config(self):
        conf = "name={}\nfreq={}\nsf={}\nchunk_size={}\nmesh_mode={}\ndebug={}".format(
                self.__name, self.connector.frequency, self.connector.sf, 
                self.__chunk_size, self.mesh_mode, self.__DEBUG)
        with open("LoRa.conf", "w") as f:
            f.write(conf)

    #This function ensures that a received message matches the criteria of any expected message.
    def __listen_receiver(self):
        packet = Packet(mesh_mode = self.mesh_mode)
        data = self.connector.recv(256)
        try:
            if not packet.load(data):   #.decode('utf-8')
                return None
        except Exception as e:
            if self.__DEBUG:
                print("Error loading: ", data, " -> ",e)
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
            self.connector.signal_estimation()
            print('LISTEN_RECEIVER() || received_content', packet.get_content())

        return packet

    def establish_connection(self, try_for=None):
        while True:
            new_sf = None
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
                            if packet.get_change_sf:
                                new_sf = packet.get_payload().decode()
                                response_packet.set_change_sf(new_sf)
                            if self.mesh_mode and packet.get_mesh():
                                response_packet.enable_mesh()
                            if packet.get_debug_hops():
                                response_packet.add_previous_hops(packet.get_message_path())
                                response_packet.add_hop(self.__name, self.connector.get_rssi(), 0)

                            self.send_response(response_packet, destination)
                            if new_sf:
                                self.change_sf(int(new_sf))
                                self.sf_trial = 3

                            return False
                        else:
                            return True
                else:
                    self.__forward(packet)
            sleep(0.01)
            gc.collect()
            if try_for is not None:
                try_for -= 1
                if try_for <= 0:
                    return False

    def send_file(self):
        while not self.__file.sent:
            destination = ''
            new_sf = None
            packet = self.__listen_receiver()
            if packet:
                if self.__is_for_me(packet=packet):
                    command = packet.get_command()
                    destination = packet.get_source()
                    if Packet.check_command(command):
                        if self.change_sf:
                            self.sf_trial = False
                            self.backup_config()
                        response_packet = None
                        if packet.get_debug_hops():
                            response_packet = Packet(mesh_mode = self.mesh_mode)
                            response_packet.set_source(self.__MAC)
                            response_packet.set_data("")
                            response_packet.enable_debug_hops()
                        else:
                            if command == Packet.CHUNK:
                                command = "{}-{}".format(Packet.CHUNK, packet.get_payload().decode())
                                response_packet = self.__handle_command(command=command)
                            elif command == Packet.OK and packet.get_change_sf():
                                new_sf = packet.get_payload().decode()
                                response_packet = Packet(self.mesh_mode)
                                response_packet.set_source(self.__MAC)
                                response_packet.set_change_sf(new_sf)
                            else:   # Metadata or OK
                                response_packet = self.__handle_command(command=command)
                        if response_packet:
                            if packet.get_mesh():
                                response_packet.enable_mesh()
                            if packet.get_debug_hops():
                                response_packet.add_previous_hops(packet.get_message_path())
                                response_packet.add_hop(self.__name, self.connector.get_rssi(), 0)

                        self.send_response(response_packet, destination)
                        if new_sf:
                            self.change_sf(int(new_sf))
                            self.sf_trial = 3
                else:
                    self.__forward(packet=packet)
            else:
                if self.sf_trial:
                    self.sf_trial -= 1
                    if self.sf_trial <= 0:
                        self.restore_sf()
                        self.sf_trial = False
        del(self.__file)
        gc.collect()
        self.__file = None

    def __handle_command(self, command: str):
        response_packet = None
        if command.startswith(Packet.OK):
            if self.__file.first_sent and not self.__file.last_sent:	# If some chunks are already sent...
                self.__file.sent_ok()
                #return None
            response_packet = Packet(self.mesh_mode)
            response_packet.set_source(self.__MAC)
            response_packet.set_ok()

        if command.startswith(Packet.METADATA):                     # handle for new file
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
                if packet.get_sleep():
                    random_sleep = 0
                else:
                    random_sleep = (urandom(1)[0] % 5 + 1) * 0.1
                if packet.get_debug_hops():
                    packet.add_hop(self.__name, self.connector.get_rssi(), random_sleep)
                packet.enable_hop()
                if random_sleep:
                    sleep(random_sleep)  # Revisar

                success = self.send_lora(packet)
                if success:
                    self.LAST_SEEN_IDS.append(packet.get_id())
                    self.LAST_SEEN_IDS = self.LAST_SEEN_IDS[-self.MAX_IDS_CACHED:]
                #else:
                #    if self.__DEBUG:
                #        print("ALREADY_FORWARDED", self.__LAST_SEEN_IDS)
        except Exception as e:
            # If packet was corrupted along the way, won't read the COMMAND part
            if self.__DEBUG:
                print("ERROR FORWARDING", e)
