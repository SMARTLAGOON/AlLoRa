from m3LoRaCTP.Nodes.Base_Node import m3LoRaCTP_Node, Packet
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


class m3LoRaCTP_Receiver(m3LoRaCTP_Node):

    def __init__(self, mesh_mode = False, debug_hops = False, connector = None, 
                    NEXT_ACTION_TIME_SLEEP = 0.1):
        m3LoRaCTP_Node.__init__(self, mesh_mode, connector = connector)

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

    def listen_to_endpoint(self, digital_endpoint, listening_time, return_file=False):
        mac = digital_endpoint.get_mac_address()
        t0 = time()
        in_time = True
        while (in_time):
            if digital_endpoint.state == "REQUEST_DATA_STATE":
                metadata, hop = self.ask_metadata(mac, digital_endpoint.get_mesh())
                digital_endpoint.set_metadata(metadata, hop, self.mesh_mode)

            elif digital_endpoint.state == "PROCESS_CHUNK_STATE":
                next_chunk = digital_endpoint.get_next_chunk()
                if next_chunk is not None:
                    data, hop = self.ask_data(mac, digital_endpoint.get_mesh(), next_chunk)
                    file = digital_endpoint.set_data(data, hop, self.mesh_mode)
                    if file and return_file:
                        return file

            elif digital_endpoint.state == "OK":
                ok, hop = self.ask_ok(mac, digital_endpoint.get_mesh())
                digital_endpoint.connected(ok, hop, self.mesh_mode)

            #elif datasource.state == "REQUEST_CONNECT":
                #pass

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