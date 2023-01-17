from m3LoRaCTP.m3LoRaCTP_Packet import Packet

class Connector:
    MAX_LENGTH_MESSAGE = 255

    def __init__(self):
        self.__MAC = "000000000000000000"

    def config(self, frequency = 868, sf=7, mesh_mode=False, debug=False, max_timeout = 6):
        self.frequency = frequency
        self.sf = sf
        self.mesh_mode = mesh_mode

        self.__WAIT_MAX_TIMEOUT = max_timeout
        self.__DEBUG = debug
        self.mesh_mode = mesh_mode

    def get_mac(self):
        return self.__MAC

    def set_sf(sf):
        pass

    def set_mesh_mode(self, mesh_mode=False):
        self.mesh_mode = mesh_mode

    def send(self, packet: Packet):
        return None

    def recv(self, size):
        return None

    def send_and_wait_response(self, packet):
        packet.set_source(self.__MAC)
        response_packet = Packet(self.__mesh_mode)
        if self.send(packet): # Success
            received_data = self.recv()
            if received_data:
                if self.__DEBUG:
                    self.signal_estimation()
                    print("WAIT_RESPONSE() || sender_reply: {}".format(received_data))
                try:
                    response_packet.load(received_data)
                    if response_packet.get_source() == packet.get_destination():
                        return response_packet
                except Exception as e:
                    if self.__DEBUG:
                        print("Corrupted packet received", e, received_data)
        return response_packet

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
