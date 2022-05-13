import network
import binascii

class Packet:

    SOURCE_HEADER = "S"
    DESTINATION_HEADER = "D"
    FORWARD_TO_HEADER = "F"
    MY_LORA_MAC = str(binascii.hexlify(network.LoRa().mac()).decode('utf-8'))

    def __init__(self, part_separator=";;;", name_separator=":::"):
        self.__source = Packet.MY_LORA_MAC
        self.__destination ="-"
        self.__forward_to = "-"

        self.__part_separator = part_separator
        self.__name_separator = name_separator

        #Payload
        self.__parts = dict()
        self.__order = list()

        self.__empty = False #FIXME Weak logic for the moment


    def get_source(self):
        return self.__source


    def get_destination(self):
        return self.__destination


    def set_destination(self, destination: str):
        self.__destination = destination


    def get_forward_to(self):
        return self.__forward_to


    def set_forward_to(self, forward_to: str):
        self.__forward_to = forward_to


    def set_part(self, name, content="-"):
        self.__parts[name] = content
        self.__order.append(name)


    def fill_part(self, name, content):
        self.__parts[name] = content


    def get_part(self, name):
        return self.__parts[name]


    def order(self, name_list):
        self.__order = name_list


    def is_empty(self):
        return self.__empty


    def get_content(self):
        if self.__empty is True:
            return None

        packet = Packet.SOURCE_HEADER + self.__name_separator + self.__source + self.__part_separator + \
                 Packet.DESTINATION_HEADER + self.__name_separator + self.__destination + self.__part_separator + \
                 Packet.FORWARD_TO_HEADER + self.__name_separator + self.__forward_to + self.__part_separator

        for i in range(len(self.__order)):
            packet += self.__order[i] + self.__name_separator + self.__parts[self.__order[i]]
            if i == len(self.__order) - 1:
                break
            else:
                packet += self.__part_separator
        return packet


    def load(self, packet: str):
        if len(packet) <= 0:
            self.__empty = True
            return

        self.__empty = False

        all_parts = packet.split(self.__part_separator)

        #Always the first three parts are source, destination and forward_to
        self.__source = all_parts[0].split(self.__name_separator)[1]
        self.__destination = all_parts[1].split(self.__name_separator)[1]
        self.__forward_to = all_parts[2].split(self.__name_separator)[1]

        for part in all_parts[3:]:
            self.set_part(part.split(self.__name_separator)[0], part.split(self.__name_separator)[1])
