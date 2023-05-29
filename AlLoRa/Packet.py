import struct
import hashlib
import binascii
try:
    from ujson import loads, dumps
except:
    from json import loads, dumps

class Packet:

    HEADER_SIZE_P2P  = 20
    HEADER_FORMAT_P2P  = "!8s8sB3s" #Source, Destination, Flags, Check Sum
    HEADER_SIZE_MESH  = 22
    HEADER_FORMAT_MESH  = "!8s8sB2s3s" #Source, Destination, Flags, ID, Check Sum

    OK = "OK"
    METADATA = "METADATA"  #"request-data-info"
    CHUNK = "CHUNK"                 #"chunk-"
    DATA = "DATA"
    COMMAND = {DATA: "00", OK: "01", CHUNK: "10", METADATA: "11"}
    COMMAND_BITS = {"00": DATA, "01": OK, "10": CHUNK, "11": METADATA}

    @staticmethod
    def check_command(command: str) -> bool:
        if command in Packet.COMMAND:
            return True
        return False

    def __init__(self, mesh_mode):
        self.mesh_mode = mesh_mode

        if not self.mesh_mode:
            self.HEADER_SIZE = self.HEADER_SIZE_P2P
            self.HEADER_FORMAT = self.HEADER_FORMAT_P2P
        else:
            self.HEADER_SIZE = self.HEADER_SIZE_MESH
            self.HEADER_FORMAT = self.HEADER_FORMAT_MESH

        self.source = ''                  # 8 Bytes mac address of the source
        self.destination = ''             # 8 Bytes mac address of the destination

        self.checksum = None              # Checksum
        self.payload = b''                # Content of the message

        self.check = None                 # True if checksum is correct with content

        ## Flags:
        self.command = None               # Type of command / or Data                           bit: 0, 1
        # Only for mesh mode
        self.mesh = False                 # Mesh On or Off for this Node                        bit: 3
        self.sleep = True                # True if should sleep before forwarding message       bit: 4
        self.hop = False                  # If packet was forwarder -> 1, else -> 0             bit: 5
        self.debug_hops = False           # Overrides payload to get path details (hops)        bit: 6
        # Change settings
        self.change_sf = False            # If True, check payload to change SF                 bit: 7

        # For mesh
        self.id = None                    # Random number from 0 to 65.535

    def set_source(self, source: str):
        self.source = source

    def get_source(self):
        return self.source

    def set_destination(self, destination: str):
        self.destination = destination

    def get_destination(self):
        return self.destination

    def get_command(self):
        return self.command

    def set_ok(self):
        self.command = "OK"

    def ask_metadata(self):
         self.command = "METADATA"

    def set_metadata(self, length, name):
        self.command = "METADATA"
        metadata = {"LENGTH" : length, "FILENAME": name}
        self.payload = dumps(metadata).encode()

    def get_payload(self):
        return self.payload

    def get_metadata(self):
        if self.command == "METADATA":
            try:
                return loads(self.payload)
            except:
                return None

    def ask_data(self, next_chunk):
        self.command = "CHUNK"
        self.payload = str(next_chunk).encode()

    def set_data(self, chunk):
        self.command = "DATA"
        self.payload = chunk

    def get_mesh(self):
        return self.mesh

    def enable_mesh(self):
        self.mesh = True

    def disable_mesh(self):
        self.mesh = False

    def enable_hop(self):
        self.hop = True

    def get_hop(self):
        return self.hop

    def get_debug_hops(self):
        return self.debug_hops

    def enable_debug_hops(self):
        self.debug_hops = True

    def disable_debug_hops(self):
        self.debug_hops = False

    def enable_sleep(self):
        self.sleep = True

    def disable_sleep(self):
        self.sleep = False

    def get_sleep(self):
        return self.sleep

    def get_change_sf(self):
        return self.change_sf

    def set_change_sf(self, sf):
        self.set_ok()
        self.change_sf = True
        self.payload = dumps(sf).encode()

    def get_message_path(self):
        if self.debug_hops:
            try:
                return loads(self.payload)
            except:
                return None

    def add_hop(self, name, rssi, time_sleep):
        hop = (name, rssi, time_sleep)
        path = self.get_message_path()
        if isinstance(path, list):
            path.append(hop)
        else:
            path = [hop]
        self.enable_debug_hops()
        self.payload = dumps(path).encode()

    def add_previous_hops(self, path):
        if isinstance(path, list):
            self.payload = dumps(path).encode()

    def set_id(self, id):
        if id <= 65535:
            self.id = id

    def get_id(self):
        return self.id

    def get_length(self):
        if len(self.payload) > 0:
            return self.HEADER_SIZE + len(self.payload)
        else:
            return self.HEADER_SIZE

    def get_checksum(self, data):
        h = hashlib.sha256(data)
        ha = binascii.hexlify(h.digest())
        return (ha[-3:])

    def get_content(self):
        if self.command in self.COMMAND:
            command_bits = self.COMMAND[self.command]

            flags = 0
            if command_bits[0] == "1":
                flags = flags | (1<<0)
            if command_bits[1] == "1":
                flags = flags | (1<<1)
            if self.mesh:
                flags = flags | (1<<3)
            if self.sleep:
                flags = flags | (1<<4)
            if self.hop:
                flags = flags | (1<<5)
            if self.debug_hops:
                flags = flags | (1<<6)
            if self.change_sf:
                flags = flags | (1<<7)

            p = self.payload
            self.checksum = self.get_checksum(p)

            if self.mesh_mode:
                try:
                    id_bytes = self.id.to_bytes(2, 'little')
                except:
                    print(self.source.encode(), self.destination.encode(), flags, self.id, self.checksum)
                #print(self.source, self.destination, flags, id_bytes, self.checksum, p)
                h = struct.pack(self.HEADER_FORMAT, self.source.encode(), self.destination.encode(), flags, id_bytes, self.checksum)
            else:
                #print(self.source, self.destination, flags,  self.checksum, p)
                h = struct.pack(self.HEADER_FORMAT, self.source.encode(), self.destination.encode(), flags,  self.checksum)

            return h+p

    def parse_flags(self, flags: int):
        c0 = "1" if (flags >> 0) & 1 == 1 else "0"
        c1 = "1" if (flags >> 1) & 1 == 1 else "0"
        self.command = self.COMMAND_BITS[c0+c1]

        self.mesh  = (flags >> 3) & 1 == 1
        self.sleep = (flags >> 4) & 1 == 1
        self.hop = (flags >> 5) & 1 == 1
        self.debug_hops = (flags >> 6) & 1 == 1
        self.change_sf = (flags >> 7) & 1 == 1

    def load(self, packet):
        header  = packet[:self.HEADER_SIZE]
        content = packet[self.HEADER_SIZE:]

        if self.mesh_mode:
            self.source, self.destination, flags,  id, self.checksum = struct.unpack(self.HEADER_FORMAT, header)
            self.id = int.from_bytes(id, "little")
        else:
             self.source, self.destination, flags, self.checksum = struct.unpack(self.HEADER_FORMAT, header)

        self.source = self.source.decode()
        self.destination = self.destination.decode()

        self.parse_flags(flags)

        self.payload = content

        self.check = self.checksum == self.get_checksum(self.payload)
        return self.check

    def get_dict(self):
        p = self.payload
        self.checksum = self.get_checksum(p)
        d = {"source" : self.source,
            "destination" : self.destination,
            "command" : self.command,
            "checksum" : self.checksum.decode(),
            "payload" : self.payload.decode(),
            "mesh" : self.mesh,
            "hop" : self.hop,
            "sleep" : self.sleep,
            "debug_hops" : self.debug_hops,
            "change_sf" : self.change_sf,
            "id" :self.id,
            }
        return d

    def load_dict(self, d):
        self.source = d["source"]
        self.destination = d["destination"]
        self.command = d["command"]
        self.checksum = d["checksum"].encode()
        self.payload = d["payload"].encode()
        self.mesh = d["mesh"]
        self.hop = d["hop"]
        self.sleep = d["sleep"]
        self.debug_hops = d["debug_hops"]
        self.change_sf = d["change_sf"]
        self.id = d["id"]

        self.check = self.checksum == self.get_checksum(self.payload)
        return self.check

if __name__ == "__main__":
    mac_address_A = "70b3d5499a76ba3f"[8:]
    mac_address_B = "70b3d54993a5bb9c"[8:]

    mesh_mode = True

    content = b"TEST..."

    s_addr = mac_address_A
    d_addr = mac_address_B

    print("P1: ")
    p = Packet(mesh_mode)
    p.set_source(s_addr)
    p.set_destination(d_addr)

    if mesh_mode:
        id = 555
        #p.set_retransmission(2)
        p.enable_mesh()
        p.enable_hop()
        p.set_id(id)

    #p.ask_data(1500)
    #p.set_data(content)
    p.set_metadata(5, "test")
    packet = p.get_content()
    print("Packet: {}".format(packet))
    print(p.get_payload())

    print("\nP2: ")
    p2 = Packet(mesh_mode)
    successfull = p2.load(packet)
    packet2 = p2.get_content()
    print("Packet loaded: {}".format(packet2))
    print(p2.get_payload())
    js = p2.get_dict()
    print(js)

    print("\nP3: ")
    p3 = Packet(mesh_mode)
    success = p3.load_dict(js)
    print(success)
    packet = p3.get_content()
    print("Packet: {}".format(packet))
    #print(p3.get_payload())
    metadata = p3.get_metadata()
    length = metadata["LENGTH"]
    filename = metadata["FILENAME"]
    print(length, filename)

    print(Packet.check_command("OK"))
    print(Packet.check_command("METADATA"))
    print(Packet.check_command("DATA"))
    print(Packet.check_command("CHUNK"))
    print(Packet.check_command("Other"))
