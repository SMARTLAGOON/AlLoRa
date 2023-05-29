from AlLoRa.Nodes.Node import Node, Packet
from AlLoRa.Digital_Endpoint import Digital_Endpoint
from time import time, sleep
try:
    from time import strftime
    def get_time():
        return strftime("%Y-%m-%d_%H:%M:%S")
except:
    from utime import localtime
    def get_time():
        tt = localtime()
        return "{}-{}-{}_{}:{}:{}".format(tt[0], tt[1], tt[2], tt[3], tt[4], tt[5])


class Requester(Node):

    def __init__(self, connector = None, config_file = "LoRa.json", debug_hops = False, NEXT_ACTION_TIME_SLEEP = 0.1):
        super().__init__(connector, config_file)

        self.debug_hops = debug_hops
        self.NEXT_ACTION_TIME_SLEEP = NEXT_ACTION_TIME_SLEEP

    def create_request(self, destination, mesh_active, sleep_mesh):
        packet = Packet(self.mesh_mode)
        packet.set_destination(destination)
        if mesh_active:
            packet.enable_mesh()
            if not sleep_mesh:
                packet.disable_sleep()
        return packet

    def ask_ok(self, packet: Packet):
        packet.set_ok()
        response_packet = self.send_request(packet)
        if self.save_hops(response_packet):
            return  (1, "hop_catch.json"), response_packet.get_hop()
        if response_packet.get_command() == Packet.OK:
            hop = response_packet.get_hop()
            return True, hop
        return None, None

    def ask_metadata(self, packet: Packet):
        packet.ask_metadata()
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
        return None, None

    def ask_data(self, packet: Packet, next_chunk):
        print("ASKING DATA")
        packet.ask_data(next_chunk)
        response_packet = self.send_request(packet)
        print("Response Packet: ", response_packet)
        print("packet command: ", response_packet.get_command())
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
                print("CHUNK + HOP: ", chunk, "->", hop)
                return chunk, hop

            except Exception as e:
                print("ASKING DATA ERROR: {}".format(e))
                return None, None
        return None, None

    def listen_to_endpoint(self, digital_endpoint: Digital_Endpoint, listening_time, 
                            print_file=False, save_file=False):
        
        mac = digital_endpoint.get_mac_address()
        sleep_mesh = digital_endpoint.get_sleep()
        t0 = time()
        in_time = True
        while (in_time):
            packet_request = self.create_request(mac, digital_endpoint.get_mesh(), sleep_mesh)

            if digital_endpoint.state == "REQUEST_DATA_STATE":
                metadata, hop = self.ask_metadata(packet_request)
                digital_endpoint.set_metadata(metadata, hop, self.mesh_mode)

            elif digital_endpoint.state == "PROCESS_CHUNK_STATE":
                next_chunk = digital_endpoint.get_next_chunk()
                print("ASKING CHUNK: {}".format(next_chunk))
                if next_chunk is not None:
                    data, hop = self.ask_data(packet_request, next_chunk)
                    file = digital_endpoint.set_data(data, hop, self.mesh_mode)
                    if file:   
                        if print_file:
                            print(file.get_content())
                        if save_file:
                            file.save(mac)

            elif digital_endpoint.state == "OK":
                ok, hop = self.ask_ok(packet_request)
                digital_endpoint.connected(ok, hop, self.mesh_mode)

            in_time = True if time() - t0 < listening_time else False
            sleep(self.NEXT_ACTION_TIME_SLEEP)

    def save_hops(self, packet):
        if packet.get_debug_hops():
            hops = packet.get_message_path()
            id = packet.get_id()
            t = get_time()  #strftime("%Y-%m-%d_%H:%M:%S")
            line = "{}: ID={} -> {}\n".format(t, id, hops)
            with open('log_rssi.txt', 'a') as log:
                log.write(line)
                #print(line)
            return True
        return False

    def ask_change_sf(self, digital_endpoint, new_sf):
        try_for = 3
        if 7 <= new_sf <= 12:
            while True:
                packet = Packet(self.mesh_mode)
                packet.set_destination(digital_endpoint.get_mac_address())
                packet.set_change_sf(new_sf)
                if digital_endpoint.get_mesh():
                    packet.enable_mesh()
                    if not digital_endpoint.get_sleep():
                        packet.disable_sleep()
                response_packet = self.send_request(packet)
                if response_packet.get_command() == Packet.OK:
                    sf_response = int(response_packet.get_payload().decode().split('"')[1])
                    print(sf_response)
                    if sf_response == new_sf:
                        return True
                else:
                    try_for -= 1
                    if try_for <= 0:
                        return False
