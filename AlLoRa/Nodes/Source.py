import gc
from AlLoRa.Nodes.Node import Node, Packet, urandom
from AlLoRa.File import CTP_File
try: 
    from utime import sleep, ticks_ms as time
except:
    from time import sleep, time

class Source(Node):

    def __init__(self, connector, config_file = "LoRa.json"):
        super().__init__(connector, config_file)
        gc.enable()

        if self.mesh_mode and self.chunk_size > 233:   # Packet size less than 255 (with Spreading Factor 7)
            self.chunk_size = 233
            if self.debug:
                print("Chunk size force down to {}".format(self.chunk_size))

        self.file = None

    def get_chunk_size(self):
        return self.chunk_size

    def got_file(self):     # Check if I have a file to send
        return self.file is not None

    def set_file(self, file : CTP_File):
        self.file = file

    def restore_file(self, file: CTP_File):
        self.set_file(file)
        self.file.first_sent = time()
        self.file.metadata_sent = True

    #This function ensures that a received message matches the criteria of any expected message.
    def listen_receiver(self):
        packet = Packet(mesh_mode = self.mesh_mode)
        data = self.connector.recv()
        try:
            if not packet.load(data):
                return None
        except Exception as e:
            if self.debug:
                print("Error loading: ", data, " -> ",e)
            return None

        if self.mesh_mode:
            try:
                packet_id = packet.get_id() #Check if already forwarded or sent by myself
                if packet_id in self.LAST_SEEN_IDS or packet_id in self.LAST_IDS:
                    if self.debug:
                        print("ALREADY_SEEN", self.LAST_SEEN_IDS)
                    return None
            except Exception as e:
                if self.debug:
                    print(e)

        if self.debug:
            self.connector.signal_estimation()
            print('LISTEN_RECEIVER() || received_content', packet.get_content())

        return packet

    def establish_connection(self, try_for=None):
        while True:
            print("establish")
            new_sf = None
            packet = self.listen_receiver()
            if packet:
                if self.is_for_me(packet):
                    command = packet.get_command()
                    if Packet.check_command(command):
                        if command != Packet.OK:
                            return True
                        response_packet = Packet(self.mesh_mode)
                        response_packet.set_source(self.MAC)
                        response_packet.set_destination(packet.get_source())
                        response_packet.set_ok()

                        if packet.get_change_sf():
                            new_sf = packet.get_payload().decode()
                            response_packet.set_change_sf(new_sf)
                        if self.mesh_mode and packet.get_mesh() and packet.get_hop():
                            response_packet.enable_mesh()
                            if not packet.get_sleep():
                                response_packet.disable_sleep()
                        if packet.get_debug_hops():
                            response_packet.add_previous_hops(packet.get_message_path())
                            response_packet.add_hop(self.name, self.connector.get_rssi(), 0)

                        self.send_response(response_packet)
                        if new_sf:
                            self.change_sf(int(new_sf))
                            self.sf_trial = 3
                        return False
                else:
                    self.forward(packet)
            gc.collect()
            if try_for is not None:
                try_for -= 1
                if try_for <= 0:
                    return False

    def send_file(self):
        while not self.file.sent:
            packet = self.listen_receiver()
            if packet:
                if self.is_for_me(packet=packet):
                    response_packet, new_sf = self.response(packet)
                    self.send_response(response_packet)
                    if new_sf:
                        self.change_sf(int(new_sf))
                        self.sf_trial = 3
                else:
                    self.forward(packet=packet)
            elif self.sf_trial:
                self.sf_trial -= 1
                if self.sf_trial <= 0:
                    self.restore_sf()
                    self.sf_trial = False
        del(self.file)
        gc.collect()
        self.file = None

    def response(self, packet):
        command = packet.get_command()
        if not Packet.check_command(command):
            return None, None

        response_packet = Packet(mesh_mode = self.mesh_mode)
        response_packet.set_source(self.MAC)
        response_packet.set_destination(packet.get_source())

        if self.mesh_mode:
            if packet.get_mesh() and packet.get_hop():
                response_packet.enable_mesh()
                if not packet.get_sleep():
                    response_packet.disable_sleep()

        new_sf = None
        if self.sf_trial:
            self.sf_trial = False
            self.backup_config()

        if packet.get_debug_hops():
            response_packet.set_data("")
            response_packet.enable_debug_hops()
            response_packet.add_previous_hops(packet.get_message_path())
            response_packet.add_hop(self.name, self.connector.get_rssi(), 0)
            return response_packet, new_sf

        if command == Packet.CHUNK:
            requested_chunk = int(packet.get_payload().decode())
            response_packet.set_data(self.file.get_chunk(requested_chunk))

            if self.debug:
                print("RC: {}".format(requested_chunk))

            if not self.file.first_sent:
                self.file.report_SST(True)
            return response_packet, new_sf

        if command == Packet.METADATA:    # handle for new file
            response_packet.set_metadata(self.file.get_length(), self.file.get_name())

            if self.file.metadata_sent:
                self.file.retransmission += 1
                if self.debug:
                    print("asked again for Metadata...")
            else:
                self.file.metadata_sent = True
            return response_packet, new_sf

        if command == Packet.OK:
            response_packet.set_ok()

            if packet.get_change_sf():
                new_sf = packet.get_payload().decode()
                response_packet.set_change_sf(new_sf)
            elif self.file.first_sent and not self.file.last_sent:	# If some chunks are already sent...
                self.file.sent_ok()
            return response_packet, new_sf

        return response_packet, new_sf

    def forward(self, packet: Packet):
        try:
            if packet.get_mesh():
                if self.debug:
                    print("FORWARDED", packet.get_content())
                
                random_sleep = 0
                if packet.get_sleep():
                    random_sleep = (urandom(1)[0] % 5 + 1) * 0.1
                    
                if packet.get_debug_hops():
                    packet.add_hop(self.name, self.connector.get_rssi(), random_sleep)
                packet.enable_hop()
                if random_sleep:
                    sleep(random_sleep)

                success = self.send_lora(packet)
                if success:
                    self.LAST_SEEN_IDS.append(packet.get_id())
                    self.LAST_SEEN_IDS = self.LAST_SEEN_IDS[-self.MAX_IDS_CACHED:]
                else:
                    if self.debug:
                        print("ALREADY_FORWARDED", self.LAST_SEEN_IDS)
        except Exception as e:
            # If packet was corrupted along the way, won't read the COMMAND part
            if self.debug:
                print("ERROR FORWARDING", e)
