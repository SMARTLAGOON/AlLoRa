import socket
import binascii
import gc
from time import sleep, time

from random import randint
from time import strftime

from lora_ctp.Packet import Packet


class LoRA_CTP_Node:
    
    MAX_LENGTH_MESSAGE = 255    # Must check if packet <= this limit to send a message

    def __init__(self, mesh_mode = False, 
            debug_hops = False, adapter = None, 
            NEXT_ACTION_TIME_SLEEP = 0.1, 
            TIME_PER_BUOY = 10):
        self.mesh_mode = mesh_mode
        self.__debug_hops = debug_hops

        self.NEXT_ACTION_TIME_SLEEP = NEXT_ACTION_TIME_SLEEP
        self.TIME_PER_BUOY = TIME_PER_BUOY

        self.adapter = adapter
        if self.adapter:
            self.adapter.set_mesh_mode(self.mesh_mode)
            self.__MAC = self.adapter.get_mac()[8:]
        else:
            from network import LoRa
            frequency = 868000000
            sf = 7
            self.__lora = LoRa(mode=LoRa.LORA, frequency=frequency,
                                region=LoRa.EU868, sf = sf)
            self.__lora_socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
            self.__lora_socket.setblocking(False)
            self.__MAC = binascii.hexlify(LoRa().mac()).decode('utf-8')[8:]
        
        self.__LAST_IDS = list()
        self.__LAST_SEEN_IDS = list()       # IDs from my mesagges
        self.__MAX_IDS_CACHED = 30          # Max number of IDs saved
        
    def get_mesh_mode(self):
        return self.mesh_mode

    def __generate_id(self):
        id = -1
        while (id in self.__LAST_IDS) or (id == -1):
            id = randint(0, 65535)

        self.__LAST_IDS.append(id)
        self.__LAST_IDS = self.__LAST_IDS[-self.__MAX_IDS_CACHED:]
        return id

    def check_id_list(self, id):
        if id not in self.__LAST_SEEN_IDS:
            self.__LAST_SEEN_IDS.append(id)    #part("ID")
            self.__LAST_SEEN_IDS = self.__LAST_SEEN_IDS[-self.__MAX_IDS_CACHED:]
            return True
        else:
            return False

    def ask_ok(self, mac_address, mesh):
        packet = Packet(self.mesh_mode) 
        packet.set_destination(mac_address)
        packet.set_ok()
        if mesh:
            packet.enable_mesh()
        response_packet = self.send_request(packet)
        if self.save_hops(response_packet):
            return  (1, "hop_catch.json"), response_packet.get_hop()
        if response_packet.get_command() == "OK":
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
        if response_packet.get_command() == "METADATA":
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
        if response_packet.get_command() == "DATA":
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

    def send_request(self, packet: Packet) -> Packet:
        #print(packet.get_content())
        if self.mesh_mode:
            packet.set_id(self.__generate_id())    #_part("ID", str(generate_id()))
            if self.__debug_hops:
                packet.enable_debug_hops()
            
        if self.adapter:
            response_packet = self.adapter.send_and_wait_response(packet)
        else:
            pass # Other way to send data (lora_socket, dragino, etc)

        return response_packet

    # LoRa methods
    """ This function returns the RSSI of the last received packet"""
    def __raw_rssi(self):
        return self.__lora.stats()[1]

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

    '''This function send a LoRA-CTP Packet using raw LoRa'''
    def __send(self, packet):
        if self.__DEBUG:
            print("SEND_PACKET() || packet: {}".format(packet.get_content()))
        if packet.get_length() <= LoRA_CTP_Node.MAX_LENGTH_MESSAGE:
            #self.__lora_socket.send(packet.get_content())	#.encode()
            return True
        else:
            print("Error: Packet too big")
            return False

    def __recv(self):
        return self.__lora_socket.recv(256)

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

    # GATEWAY METHODS:
    def set_datasources(self, datasources):
        self.datasources = datasources

    def check_datasources(self):
        while True:
            for datasource in self.datasources:
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

                    in_time = True if time() - t0 < self.TIME_PER_BUOY else False
                    sleep(self.NEXT_ACTION_TIME_SLEEP)
