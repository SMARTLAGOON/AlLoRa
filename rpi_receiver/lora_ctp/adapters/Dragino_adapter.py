import time

from lora_ctp.Packet import Packet
from lora_ctp.adapters.SX127x import board_config, constants
from lora_ctp.adapters.SX127x import LoRa
from lora_ctp.adapters.Adapter import Adapter


class Dragino_adapter(Adapter):
    MAX_LENGTH_MESSAGE = 255

    def __init__(self, frequency=868, sf=7, mesh_mode=False, debug=False, max_timeout=10):

        super().__init__()
        board_config.BOARD.setup()
        self.lora = LoRa.LoRa(verbose=False,
                              do_calibration=True,
                              calibration_freq=868,
                              sf=sf,
                              cr=constants.CODING_RATE.CR4_5,
                              freq=frequency)
        self.__WAIT_MAX_TIMEOUT = max_timeout
        self.__DEBUG = debug
        self.__mesh_mode = mesh_mode
        self.lora.setblocking(False)


    def __signal_estimation(self):
        percentage = 0
        rssi = self.lora.get_rssi_value()
        if (rssi >= -50):
            percentage = 100
        elif (rssi <= -50) and (rssi >= -100):
            percentage = 2 * (rssi + 100)
        elif (rssi < 100):
            percentage = 0
        print('SIGNAL STRENGTH', percentage, '%')

    def send_and_wait_response(self, packet):
        packet.set_source(self.get_mac())  # Adding mac address to packet

        self.lora.setblocking(True)
        success = self.__send(packet)
        self.lora.setblocking(False)

        response_packet = Packet(self.__mesh_mode)  # = mesh_mode
        if success:
            timeout = self.__WAIT_MAX_TIMEOUT
            received = False
            received_data = b''
            while (timeout > 0 or received is True):
                if self.__DEBUG:
                    print("WAIT_RESPONSE() || quedan {} segundos timeout".format(timeout))
                try:
                    self.lora.settimeout(timeout)
                    received_data = self.__recv(256)
                    if received_data:
                        if self.__DEBUG:
                            self.__signal_estimation()
                            print("WAIT_WAIT_RESPONSE() || sender_reply: {}".format(received_data))
                        # if received_data.startswith(b'S:::'):
                        try:
                            response_packet = Packet(self.__mesh_mode)  # = mesh_mode
                            response_packet.load(received_data)  # .decode('utf-8')
                            if response_packet.get_source() == packet.get_destination():
                                received = True
                                break
                            else:
                                response_packet = Packet(self.__mesh_mode)  # = mesh_mode
                        except Exception as e:
                            print("Corrupted packet received", e)
                except TimeoutError as e:
                    print("TimeOut!", e)
                timeout -= 1
        return response_packet

    def __send(self, packet):
        if self.__DEBUG:
            print("SEND_PACKET() || packet: {}".format(packet.get_content()))
        if packet.get_length() <= Dragino_adapter.MAX_LENGTH_MESSAGE:
            self.lora.send(packet.get_content())  # .encode()
            return True
        else:
            print("Error: Packet too big")
        return False

    def get_rssi(self):
        return self.lora.get_pkt_rssi_value()

    def __recv(self, size):
        packet = self.lora.recv(size)
        return packet