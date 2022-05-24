import network
import binascii
from ujson import dumps, loads

class Packet:

    SOURCE_HEADER = "S"
    DESTINATION_HEADER = "D"
    MESH_HEADER = "M"
    MY_LORA_MAC = binascii.hexlify(network.LoRa().mac()).decode('utf-8')

    def __init__(self, part_separator=";;;", name_separator=":::", mesh_mode = False):
        self.__source = Packet.MY_LORA_MAC
        self.__destination ="-"
        self.__mesh = "0"

        self.__part_separator = part_separator
        self.__name_separator = name_separator

        #Payload
        self.__parts = dict()
        self.__order = list()

        self.__empty = True
        self.__mesh_mode = mesh_mode

    def get_source(self):
        return self.__source

    #TODO Update the object in the rest of code
    def set_source(self, source: str):
        self.__source = source

    def get_destination(self):
        return self.__destination

    def set_destination(self, destination: str):
        self.__destination = destination

    def get_mesh(self):
        return self.__mesh

    def enable_mesh(self):
        self.__mesh = "1"
        self.set_part("M", self.__mesh)

    def disable_mesh(self):
        self.__mesh = "0"
        self.__parts["M"] = self.__mesh

    def set_part(self, name, content="-"):
        self.__parts[name] = content
        self.__order.append(name)   #FIX ME hacer idempotente

    def add_hop(self, mac, rssi, time_sleep):
        metadata = {"MAC" : mac, "R": rssi, "T": time_sleep}
        print(rssi)
        if "H" in self.__order:
            hops = loads(self.__parts["H"])
            metadata = hops.append(metadata)
        self.set_part("H", dumps(metadata))


    def fill_part(self, name, content):
        self.__parts[name] = content

    def get_part(self, name):
        return self.__parts[name]

    def order(self, name_list):
        self.__order = name_list

    def is_empty(self):
        return self.__empty

    def get_content(self):
        packet = Packet.SOURCE_HEADER + self.__name_separator + self.__source + self.__part_separator + \
                 Packet.DESTINATION_HEADER + self.__name_separator + self.__destination + self.__part_separator

        if self.__mesh_mode:
            packet += Packet.MESH_HEADER + self.__name_separator + self.__mesh + self.__part_separator

        for i in range(len(self.__order)):
            packet += self.__order[i] + self.__name_separator + str(self.__parts[self.__order[i]])
            if i == len(self.__order) - 1:
                break
            else:
                packet += self.__part_separator
        return packet

    def load(self, packet: str):
        try:
            if len(packet) <= 0:
                self.__empty = True
                return

            all_parts = packet.split(self.__part_separator)
            #print(all_parts)
            #Always the first three parts are source, destination and mesh
            self.__source = all_parts[0].split(self.__name_separator)[1]
            self.__destination = all_parts[1].split(self.__name_separator)[1]
            if self.__mesh_mode:
                self.__mesh = all_parts[2].split(self.__name_separator)[1]
                next = 3
            else:
                next = 2

            for part in all_parts[next:]:
                self.set_part(part.split(self.__name_separator)[0], part.split(self.__name_separator)[1])
            return True
        except Exception as e:
            return False
