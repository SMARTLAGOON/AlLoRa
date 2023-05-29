from AlLoRa.File import CTP_File

class Digital_Endpoint:

    REQUEST_DATA_STATE = "REQUEST_DATA_STATE"
    PROCESS_CHUNK_STATE = "PROCESS_CHUNK_STATE"
    OK = "OK"

    def __init__(self, name: str, mac_address: str, active: bool = True, sleep_mesh: bool = True,
                        MAX_RETRANSMISSIONS_BEFORE_MESH: int = 10):
        self.name = name
        self.mac_address = mac_address[-8:]
        self.active = active
        self.current_file = None

        self.state = Digital_Endpoint.OK

        self.mesh = False
        self.sleep_mesh = sleep_mesh
        self.retransmission_counter = 0
        self.MAX_RETRANSMISSIONS_BEFORE_MESH = MAX_RETRANSMISSIONS_BEFORE_MESH

    def get_name(self):
        return self.name

    def get_mac_address(self):
        return self.mac_address

    def get_mesh(self):
        return self.mesh

    def is_active(self):
        return self.active

    def enable_mesh(self):
        self.mesh = True
        print("Node {}: ENABLING MESH".format(self.name))

    def disable_mesh(self):
        self.mesh = False
        self.retransmission_counter = 0
        print("Node {}: DISABLING MESH".format(self.name))

    def get_sleep(self):
        return self.sleep_mesh

    def count_retransmission(self):
        if not self.get_mesh():
            self.retransmission_counter += 1
            if self.retransmission_counter >= self.MAX_RETRANSMISSIONS_BEFORE_MESH:
                self.enable_mesh()

    def reset_retransmission_counter(self, hop): #packet
        if not self.get_mesh():                        # If mesh mode is deactivated and I receive a message from this node
            self.retransmission_counter = 0           # Reset counter, going well...
        else:
            if not hop:
                self.disable_mesh()

    def set_current_file(self, file: CTP_File):
        self.current_file = file

    def get_current_file(self):
        return self.current_file

    def connected(self, ok, hop, mesh_mode):
        if ok:
            if mesh_mode:
                self.reset_retransmission_counter(hop)
            self.state = Digital_Endpoint.REQUEST_DATA_STATE
        else:
            if mesh_mode:
                self.count_retransmission()
        
    def set_metadata(self, metadata, hop, mesh_mode):
        if metadata:
            new_file = CTP_File(name = metadata[1], length = metadata[0])
            self.set_current_file(new_file)
            if mesh_mode:
                self.reset_retransmission_counter(hop)
            
            self.state = Digital_Endpoint.PROCESS_CHUNK_STATE
            print("State:{}".format(self.state))
        else:
            if mesh_mode:
                self.count_retransmission()

    def get_next_chunk(self):
        try:
            self.current_chunk = self.current_file.get_missing_chunks()[0]
            return self.current_chunk
        except Exception as e:
            print("ERROR IN GET_NEXT_CHUNK: {}".format(e))
            return None

    def set_data(self, data, hop, mesh_mode):  
        if data:
            self.current_file.add_chunk(self.current_chunk, data)
            if mesh_mode:
                self.reset_retransmission_counter(hop)
        else:
            if mesh_mode:
                self.count_retransmission()
        
        if len(self.current_file.get_missing_chunks()) <= 0:
            self.state = Digital_Endpoint.OK
            return self.current_file
