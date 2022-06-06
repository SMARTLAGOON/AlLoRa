import struct
import hashlib
import binascii
from json import loads, dumps

class Packet:

    HEADER_SIZE_P2P  = 20
    HEADER_FORMAT_P2P  = "!8s8sB3s" #Source, Destination, Flags, Check Sum
    HEADER_SIZE_MESH  = 22
    HEADER_FORMAT_MESH  = "!8s8sB2s3s" #Source, Destination, Flags, ID, Check Sum
    COMMAND = {"DATA": "00", "OK": "01", "CHUNK": "10", "METADATA": "11"}
    COMMAND_BITS = {"00": "DATA", "01": "OK", "10": "CHUNK", "11": "METADATA"}

    def __init__(self, mesh_mode):
        self.__mesh_mode = mesh_mode
        self.__empty = False    # Should be true and then change to False (but for now True..)

        if not self.__mesh_mode:
            self.HEADER_SIZE = self.HEADER_SIZE_P2P
            self.HEADER_FORMAT = self.HEADER_FORMAT_P2P
        else:
            self.HEADER_SIZE = self.HEADER_SIZE_MESH
            self.HEADER_FORMAT = self.HEADER_FORMAT_MESH

        self.__source = b''            # 8 Bytes mac address of the source
        self.__destination = b''       # 8 Bytes mac address of the destination
        self.__command = None           # Type of command / or Data
        self.__retransmission = False     # True if already sent one or more times
        self.__checksum = None          # Checksum
        self.__payload = b''           # Content of the message

        self.__check = None               # True if checksum is correct with content

        # Only for mesh mode
        self.__mesh = False  # Mesh On or Off for this Node
        self.__hop = False   # If packet was forwarder -> 1, else -> 0
        self.__id = None    # Random number from 0 to 65.535

        self.__hops = None

    def set_source(self, source: str):
        self.__source = source.encode()

    def get_source(self):
        return self.__source

    def set_destination(self, destination: str):
        self.__destination = destination.encode()

    def get_destination(self):
        return self.__destination

    def get_command(self):
        return self.__command

    def ask_metadata(self):
         self.__command = "METADATA"

    def set_metadata(self, length, name):
        self.__command = "METADATA"
        metadata = {"LENGTH" : length, "FILENAME": name}
        self.__payload = dumps(metadata)

    def get_payload(self):
        return self.__payload

    def get_metadata(self):
        if self.__command == "METADATA":
            try:
                metadata = loads(self.__payload)
                return metadata
            except:
                return None

    def ask_data(self, next_chunk):
        self.__command = "CHUNK"
        self.__payload = str(next_chunk).encode()

    def set_data(self, chunk):
        self.__command = "DATA"
        self.__payload = chunk

    def get_retransmission(self):
        return self.__retranmission

    def set_retransmission(self, retr):
        if retr > 0:
            self.__retranmission = True
        else:
            self.__retranmission = False

    def get_mesh(self):
        return self.__mesh

    def enable_mesh(self):
        self.__mesh = True

    def disable_mesh(self):
        self.__mesh = False

    def enable_hop(self):
        self.__hop = True

    def get_hop(self):
        return self.__hop

    def add_hop(self, name, rssi, time_sleep):
        metadata = {"N" : name, "R": rssi, "T": time_sleep}
        #print(rssi)
        if self.__hops:
            hops = loads(self.__hops)
            hops.append(metadata)
        else:
            hops = []
            hops.append(metadata)
        self.__hops = dumps(hops)

    def set_id(self, id):
        print(id)
        if id < 65535:
            self.__id = id

    def get_id(self):
        return self.__id

    def is_empty(self):
        return self.__empty

    def get_lenght(self):
        if len(self.__payload) > 0:
            return self.HEADER_SIZE + len(self.__payload)
        else:
            return self.HEADER_SIZE

    def __get_checksum(self, data):
        h = hashlib.sha256(data)
        ha = binascii.hexlify(h.digest())
        return (ha[-3:])

    def get_content(self):
        print("COMMAND: ", self.__command)
        if self.__command in self.COMMAND:
            command_bits = self.COMMAND[self.__command]

            flags = 0
            if command_bits[0] == "1":
                flags = flags | (1<<0)
            if command_bits[1] == "1":
                flags = flags | (1<<1)
            if self.__retransmission:
                flags = flags | (1<<2)
            if self.__mesh:
                flags = flags | (1<<4)
            if self.__hop:
                flags = flags | (1<<6)

            #if len(self.__payload) > 0:
            #else:
                #p = b''
            p = self.__payload
            self.__checksum = self.__get_checksum(p)
            if self.__mesh_mode:
                id_bytes = self.__id.to_bytes(2, 'little')
                print(self.__source, self.__destination, flags, id_bytes, self.__checksum)
                h = struct.pack(self.HEADER_FORMAT,self.__source, self.__destination, flags, id_bytes, self.__checksum)
            else:
                print(self.__source, self.__destination, flags,  self.__checksum)
                h = struct.pack(self.HEADER_FORMAT,  self.__source, self.__destination, flags,  self.__checksum)

            return h+p

    def load(self, packet):
        header  = packet[:self.HEADER_SIZE]
        content = packet[self.HEADER_SIZE:]

        if self.__mesh_mode:
            self.__source, self.__destination, flags,  id, self.__checksum = struct.unpack(self.HEADER_FORMAT, header)
            self.__id = int.from_bytes(id, "little")
            print("id -> ", self.__id)
        else:
             self.__source, self.__destination, flags, self.__checksum = struct.unpack(self.HEADER_FORMAT, header)

        c0 = "1" if (flags >> 0) & 1 == 1 else "0"
        c1 = "1" if (flags >> 1) & 1 == 1 else "0"
        self.__command = self.COMMAND_BITS[c0+c1]
        self.__retranmission = (flags >> 2) & 1 == 1
        self.__mesh  = (flags >> 4) & 1 == 1
        self.__hop = (flags >> 6) & 1 == 1

        #if (content == b''):
        #   self.__payload = b''
        #else:
        self.__payload = content

        self.__check = self.__checksum == self.__get_checksum(self.__payload)
        return self.__check

    def get_dict(self):
        p = self.__payload
        self.__checksum = self.__get_checksum(p)
        d = {"source" : self.__source.decode(),
            "destination" : self.__destination.decode(),
            "command" : self.__command,
            "retransmission" : self.__retransmission,
            "checksum" : self.__checksum.decode(),
            "payload" : self.__payload.decode(),
            "mesh" : self.__mesh,
            "hop" : self.__hop,
            "id" :self.__id,
            }
        print(d)
        return d

    def load_dict(self, d):
        self.__source = d["source"].encode()
        self.__destination = d["destination"].encode()
        self.__command = d["command"]
        self.__retransmission = d["retransmission"]
        self.__checksum = d["checksum"].encode()
        self.__payload = d["payload"].encode()
        self.__mesh = d["mesh"]
        self.__hop = d["hop"]
        self.__id = d["id"]

        self.__check = self.__checksum == self.__get_checksum(self.__payload)
        return self.__check

if __name__ == "__main__":
    mac_address_A = "70b3d5499a76ba3f"[8:]
    mac_address_B = "70b3d54993a5bb9c"[8:]

    mesh_mode = False

    content = b"TEST..."

    s_addr = mac_address_A
    d_addr = mac_address_B


    p = Packet(mesh_mode)
    p.set_source(s_addr)
    p.set_destination(d_addr)

    if mesh_mode:
        id = 555
        p.set_retransmission(2)
        p.enable_mesh()
        p.enable_hop()
        p.set_id(id)

    #p.ask_data(1500)
    p.set_data(content)
    packet = p.get_content()
    print("Packet: {}".format(packet))
    print(p.get_payload())

    p2 = Packet(mesh_mode)
    successfull = p2.load(packet)
    packet2 = p2.get_content()
    print("Packet loaded: {}".format(packet2))
    print(p2.get_payload())
    js = p2.get_dict()
    print(js)

    p3 = Packet(mesh_mode)
    success = p3.load_dict(js)
    print(success)
    packet = p3.get_content()
    print("Packet: {}".format(packet))
    print(p3.get_payload())
