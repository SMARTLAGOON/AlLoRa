from mLoRaCTP.mLoRaCTP_Packet import Packet

class Connector:
    MAX_LENGTH_MESSAGE = 255

    def __init__(self):
        self.mesh_mode = False
        self.__MAC = "000000000000000000"

    def get_mac(self):
        return self.__MAC

    def set_mesh_mode(self, mesh_mode=False):
        self.mesh_mode = mesh_mode

    def send(self, packet: Packet):
        pass

    def recv(self, size):
        pass

    def send_and_wait_response(self, packet: Packet):
        pass

    """ This function returns the RSSI of the last received packet"""
    def get_rssi(self):
        return 0

    def signal_estimation(self):
        percentage = 0
        rssi = self.get_rssi()
        if (rssi >= -50):
            percentage = 100
        elif (rssi <= -50) and (rssi >= -100):
            percentage = 2 * (rssi + 100)
        elif (rssi < 100):
            percentage = 0
        print('SIGNAL STRENGTH', percentage, '%')