from mLoRaCTP.Nodes.Base_Node import mLoRaCTP_Node, Packet
from time import time, sleep, strftime

class mLoRaCTP_Receiver(mLoRaCTP_Node):

    def __init__(self, mesh_mode = False, debug_hops = False, connector = None, 
                    NEXT_ACTION_TIME_SLEEP = 0.1):
        mLoRaCTP_Node.__init__(self, mesh_mode, debug_hops, connector = connector)

        self.debug_hops = debug_hops
        self.NEXT_ACTION_TIME_SLEEP = NEXT_ACTION_TIME_SLEEP

    def ask_ok(self, mac_address, mesh):
        packet = Packet(self.mesh_mode) 
        packet.set_destination(mac_address)
        packet.set_ok()
        if mesh:
            packet.enable_mesh()
        response_packet = self.send_request(packet)
        if self.save_hops(response_packet):
            return  (1, "hop_catch.json"), response_packet.get_hop()
        if response_packet.get_command() == Packet.OK:
            hop = response_packet.get_hop()
            return True, hop
        else:
            return None, None

    def ask_metadata(self, mac_address, mesh):
        packet = Packet(self.mesh_mode) 
        packet.set_destination(mac_address)
        packet.ask_metadata()
        if mesh:
            packet.enable_mesh()
        response_packet = self.send_request(packet)
        if self.save_hops(response_packet):
            return  (1, "hop_catch.json"), response_packet.get_hop()
        if response_packet.get_command() == Packet.METADATA:
            try:
                metadata = response_packet.get_metadata()
                hop = response_packet.get_hop()
                length = metadata["LENGTH"]
                filename = metadata["FILENAME"]
                return (length, filename), hop
            except:
                return None, None
        else:
            return None, None

    def ask_data(self, mac_address, mesh, next_chunk):
        packet = Packet(self.mesh_mode) 
        packet.set_destination(mac_address)
        packet.ask_data(next_chunk)
        if mesh:
            packet.enable_mesh()
        response_packet = self.send_request(packet)
        if self.save_hops(response_packet):
            return b"0", response_packet.get_hop()
        if response_packet.get_command() == Packet.DATA:
            try: 
                if self.mesh_mode:
                    id = response_packet.get_id()
                    if not self.check_id_list(id):
                        return None, None
                chunk = response_packet.get_payload()
                hop = response_packet.get_hop()
                return chunk, hop

            except:
                return None, None
        else:
            return None, None

    """This function waits for a message to be received from a sender using raw LoRa"""
    def send_and_wait_response(self, packet):
        packet.set_source(self.__MAC)		# Adding mac address to packet
        success = self.__send(packet)
        response_packet = Packet(self.mesh_mode)
        if success:
            timeout = self.__WAIT_MAX_TIMEOUT
            received = False
            received_data = b''
            while(timeout > 0 or received is True):
                if self.__DEBUG:
                    print("WAIT_RESPONSE() || quedan {} segundos timeout".format(timeout))
                received_data = self.__recv()
                if received_data:
                    if self.__DEBUG:
                        self.__signal_estimation()
                        print("WAIT_WAIT_RESPONSE() || sender_reply: {}".format(received_data))
                    #if received_data.startswith(b'S:::'):
                    try:
                        response_packet = Packet(self.mesh_mode)	# = mesh_mode
                        response_packet.load(received_data)	#.decode('utf-8')
                        if response_packet.get_source() == packet.get_destination():
                            received = True
                            break
                        else:
                            response_packet = Packet(self.mesh_mode)	# = mesh_mode
                    except Exception as e:
                        print("Corrupted packet received", e)
                time.sleep(0.01)
                timeout = timeout - 1
        return response_packet

    def listen_datasource(self, datasource, listening_time):
        mac = datasource.get_mac_address()
        t0 = time()
        in_time = True
        while (in_time):
            if datasource.state == "REQUEST_DATA_STATE":
                metadata, hop = self.ask_metadata(mac, datasource.get_mesh())
                datasource.set_metadata(metadata, hop, self.mesh_mode)

            elif datasource.state == "PROCESS_CHUNK_STATE":
                next_chunk = datasource.get_next_chunk()
                if next_chunk is not None:
                    data, hop = self.ask_data(mac, datasource.get_mesh(), next_chunk)
                    datasource.set_data(data, hop, self.mesh_mode)

            elif datasource.state == "OK":
                ok, hop = self.ask_ok(mac, datasource.get_mesh())
                datasource.connected(ok, hop, self.mesh_mode)

            #elif datasource.state == "REQUEST_CONNECT":
                #pass

            in_time = True if time() - t0 < listening_time else False
            sleep(self.NEXT_ACTION_TIME_SLEEP)

    def save_hops(self, packet):
        if packet.get_debug_hops():
            hops = packet.get_message_path()
            id = packet.get_id()
            t = strftime("%Y-%m-%d_%H:%M:%S")
            line = "{}: ID={} -> {}\n".format(t, id, hops)
            with open('log_rssi.txt', 'a') as log:
                log.write(line)
                #print(line)
            return True
        return False