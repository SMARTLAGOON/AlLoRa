from lora_ctp.Packet import Packet

class Adapter:

    def __init__(self):
        self.__mesh_mode = False

    def get_mac(self):
        return "000000000"

    def set_mesh_mode(self, mesh_mode=False):
        self.__mesh_mode = mesh_mode

    def send_and_wait_response(self, packet: Packet):
        pass