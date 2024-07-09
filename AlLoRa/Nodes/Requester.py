import gc
from AlLoRa.Nodes.Node import Node, Packet
from AlLoRa.Digital_Endpoint import Digital_Endpoint

try:
    import os
    from time import strftime, time, sleep
    def get_time():
        return strftime("%Y-%m-%d_%H:%M:%S")
except:
    import uos as os
    from utime import localtime, ticks_ms as time, sleep, sleep_ms
    def get_time():
        tt = localtime()
        return "{}-{}-{}_{}:{}:{}".format(tt[0], tt[1], tt[2], tt[3], tt[4], tt[5])


class Requester(Node):

    def __init__(self, connector = None, config_file = "LoRa.json", debug_hops = False, NEXT_ACTION_TIME_SLEEP = 0.1):
        super().__init__(connector, config_file)
        gc.enable()
        # JSON Example:
        # {
        #     "name": "G",
        #     "frequency": 868,
        #     "sf": 7,
        #     "mesh_mode": false,
        #     "debug": false,
        #     "min_timeout": 0.5,
        #     "max_timeout": 6,
        #     "result_path": "Results",
        # }
        
        self.debug_hops = debug_hops
        self.NEXT_ACTION_TIME_SLEEP = NEXT_ACTION_TIME_SLEEP
        if self.config:
            self.result_path = self.config.get('result_path', "Results")
            try:
                os.mkdir(self.result_path)
            except Exception as e:
                if self.debug:
                    print("Error creating result path: {}".format(e))

        self.status["SMAC"] = "-"   # Source MAC
        self.time_request = time()

    def create_request(self, destination, mesh_active, sleep_mesh):
        packet = Packet(self.mesh_mode)
        packet.set_destination(destination)
        if mesh_active:
            packet.enable_mesh()
            if not sleep_mesh:
                packet.disable_sleep()
        return packet

    def send_request(self, packet: Packet) -> Packet:
        if self.mesh_mode:
            packet.set_id(self.generate_id())
            if self.debug_hops:
                packet.enable_debug_hops()

        self.time_since_last_request = time() - self.time_request
        self.time_request = time()
        response_packet, packet_size_sent, packet_size_received, time_pr = self.connector.send_and_wait_response(packet)

        if self.subscribers:
            self.status['PSizeS'] = packet_size_sent
            self.status['PSizeR'] = packet_size_received
            self.status['TimePR'] = time_pr * 1000  # Time in ms
            self.status['TimeBtw'] = self.time_since_last_request * 1000  # Time in ms
            self.status['RSSI'] = self.connector.get_rssi()
            self.status['SNR'] = self.connector.get_snr()
            if response_packet is None:
                self.status['Retransmission'] += 1
                if packet_size_received > 0:
                    self.status['CorruptedPackets'] += 1

        return response_packet

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
                if self.subscribers:
                    self.status['File'] = filename
                return (length, filename), hop
            except:
                return None, None
        return None, None

    def ask_data(self, packet: Packet, next_chunk):
        packet.ask_data(next_chunk)
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
                if self.debug and hop:
                    print("CHUNK + HOP: ", chunk, "->", hop)
                return chunk, hop

            except Exception as e:
                if self.debug:
                    print("ASKING DATA ERROR: {}".format(e))
                return None, None
        return None, None

    def listen_to_endpoint(self, digital_endpoint: Digital_Endpoint, listening_time=None, 
                            print_file=False, save_file=False, one_file=False):
        stop = False
        mac = digital_endpoint.get_mac_address()
        if self.subscribers:
            self.status['SMAC'] = mac
        save_to = self.result_path + "/" + mac
        sleep_mesh = digital_endpoint.get_sleep()
        t0 = time()
        if listening_time is None:
            listening_time = float('inf')   # Infinite listening time
        end_time = t0 + listening_time
        while time() < end_time:
            t0 = 0
            try: 
                packet_request = self.create_request(mac, digital_endpoint.get_mesh(), sleep_mesh)

                if digital_endpoint.state == "REQUEST_DATA_STATE":
                    metadata, hop = self.ask_metadata(packet_request)
                    t0 = time()
                    digital_endpoint.set_metadata(metadata, hop, self.mesh_mode, save_to)

                elif digital_endpoint.state == "PROCESS_CHUNK_STATE":
                    next_chunk = digital_endpoint.get_next_chunk()
                    if next_chunk is not None:
                        if self.debug:
                            print("ASKING CHUNK: {}".format(next_chunk))
                        data, hop = self.ask_data(packet_request, next_chunk)
                        t0 = time()
                        self.status['Chunk'] = digital_endpoint.file_reception_info["total_chunks"] - next_chunk
                        file = digital_endpoint.set_data(data, hop, self.mesh_mode)
                        if file:
                            # We send a final OK to the endpoint
                            final_ok = self.create_request(mac, digital_endpoint.get_mesh(), sleep_mesh)
                            final_ok.set_ok()
                            final_ok.set_source(self.connector.get_mac())
                            sleep(1)
                            self.send_lora(final_ok)
                            self.status['Chunk'] = "DONE"
                            if print_file:
                                print(file.get_content())
                            if save_file:
                                file.save(save_to)
                            if one_file:
                                stop = True

                elif digital_endpoint.state == "OK":
                    ok, hop = self.ask_ok(packet_request)
                    t0 = time()
                    digital_endpoint.connected(ok, hop, self.mesh_mode)

            except Exception as e:
                if self.debug:
                    print("LISTEN_TO_ENDPOINT ERROR: {}".format(e))

            finally:
                if self.subscribers:
                    self.status['Status'] = digital_endpoint.state
                    self.notify_subscribers()

                gc.collect()
                dt = time() - t0    # Time to process the request in ms
                sleep_time = self.NEXT_ACTION_TIME_SLEEP - (dt * 1000)
                if sleep_time > 0:
                    sleep(sleep_time)
                
                if stop:
                    break

    def save_hops(self, packet):
        if packet is None:
            return False
        if packet.get_debug_hops():
            hops = packet.get_message_path()
            id = packet.get_id()
            t = get_time()  #strftime("%Y-%m-%d_%H:%M:%S")
            line = "{}: ID={} -> {}\n".format(t, id, hops)
            with open('log_rssi.txt', 'a') as log:
                log.write(line)
            return True
        return False

    def ask_change_sf(self, digital_endpoint, new_sf):
        try_for = 3
        if 7 <= new_sf <= 12:
            while True:
                packet = Packet(self.mesh_mode)
                packet.set_destination(digital_endpoint.get_mac_addsress())
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

    def ask_change_rf(self, digital_endpoint, new_config):
        try_for = 20
        new_config = [new_config.get("freq", None), new_config.get("sf", None), 
                        new_config.get("bw", None), new_config.get("cr", None), 
                        new_config.get("tx_power", None), 
                        new_config.get("chunk_size", None)] # Chunk size not yet implemented
        config = self.connector.get_rf_config()
        print("Current config: ", config)
        print("New config: ", new_config)
        # Only change the values that are different from the current configuration
        new_freq = new_config[0] if new_config[0] != config[0] else None
        new_sf = new_config[1] if new_config[1] != config[1] else None
        new_bw = new_config[2] if new_config[2] != config[2] else None
        new_cr = new_config[3] if new_config[3] != config[3] else None
        new_tx_power = new_config[4] if new_config[4] != config[4] else None
        while True:
            packet = Packet(self.mesh_mode)
            packet.set_destination(digital_endpoint.get_mac_address())
            changes = packet.set_change_rf({"freq": new_freq, "sf": new_sf, 
                                            "bw": new_bw, "cr": new_cr, 
                                            "tx_power": new_tx_power})
            if not changes:
                return False
            if digital_endpoint.get_mesh():
                packet.enable_mesh()
                if not digital_endpoint.get_sleep():
                    packet.disable_sleep()
            response_packet = self.send_request(packet)
            try:
                if response_packet.get_command() == Packet.OK:
                    new_config = response_packet.get_config()
                    if self.debug:
                        print("OK and changing config to: ", new_config)
                    # frequency=new_config.get('freq', None)
                    # sf=new_config.get('sf', None)
                    # bw=new_config.get("bw", None)
                    # cr=new_config.get("cr", None)
                    # tx_power=new_config.get("tx_power", None)
                    #changed = self.change_rf_config(frequency=frequency, sf=sf, bw=bw, cr=cr, tx_power=tx_power)
                    changed = self.change_rf_config(new_config)
                    if not changed:
                        return False
                        #raise Exception("Error changing config")
                    return True
                else:
                    try_for -= 1
                    if try_for <= 0:
                        return False
            except Exception as e:
                if self.debug:
                    print("Error changing RF config: ", e)
                try_for -= 1
                if try_for <= 0:
                    return False




