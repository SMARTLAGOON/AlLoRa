from AlLoRa.Packet import Packet
import gc
from math import ceil
from AlLoRa.utils.time_utils import get_time, current_time_ms as time, sleep, sleep_ms
from AlLoRa.utils.debug_utils import print
from AlLoRa.utils.os_utils import os
from os import urandom

class Connector:
    MAX_LENGTH_MESSAGE = 255

    def __init__(self):
        self.MAC = "00000000"
        self.observed_min_timeout = float('inf')
        self.debug = False

    def config(self, config_json):
        # JSON Example:
        # {
        #     "name": "N",
        #     "frequency": 868,
        #     "sf": 7,
        #     "mesh_mode": false,
        #     "debug": false,
        #     "min_timeout": 0.5,
        #     "max_timeout": 6
        # }
        self.config_parameters = config_json
        if self.config_parameters:
            self.name = self.config_parameters.get('name', "N")
            self.debug = self.config_parameters.get('debug', False)

            self.frequency = self.config_parameters.get('freq', 868)    # 868 MHz
            self.sf = self.config_parameters.get('sf', 7)               # SF7
            self.bw = self.config_parameters.get("bandwidth", 125)            # 125 kHz
            self.cr = self.config_parameters.get("coding_rate", 1)            # 4/5
            self.tx_power = self.config_parameters.get("tx_power", 14)         # 14 dBm

            self.mesh_mode = self.config_parameters.get('mesh_mode', False)
            self.short_mac = self.config_parameters.get('short_mac', False)

            self.min_timeout = self.config_parameters.get('min_timeout', 0.5)
            self.max_timeout = self.config_parameters.get('max_timeout', 6)
            self.timeout_delta = self.config_parameters.get('timeout_delta', 1)  # Delta for processing times
        
            # Calculate initial adaptive timeouts
            self.update_timeouts()

            self.adaptive_timeout = self.max_timeout
            self.backup_timeout = self.adaptive_timeout
            self.backup_rf_config()
        else:
            if self.debug:
                print("Error: No config parameters")

    def get_max_payload_size(self):
        if self.sf < 11:
            return 255
        elif self.sf == 11:
            return 111
        elif self.sf == 12:
            return 30   #51

    def update_timeouts(self):
        # Calculate the min and max timeouts based on the ToA for the current RF settings
        #max_toa = self.calculate_toa(self.sf, self.bw, self.cr, 255)  # Max payload
        self.max_payload_size = self.get_max_payload_size()
        min_toa = self.calculate_toa(self.sf, self.bw, self.cr, self.max_payload_size)   # Max payload
        max_toa = min_toa * 2
        self.min_timeout = min_toa + self.timeout_delta # Convert ms to seconds
        self.max_timeout = max_toa + self.timeout_delta  # Convert ms to seconds and add delta for processing times
        if self.debug:
            print("Updated timeouts: Min: {} s, Max: {} s".format(self.min_timeout, self.max_timeout))

    def calculate_toa(self, sf, bw, cr, payload_size):
        if self.debug:
            print("TOA with SF:", sf, "BW:", bw, "CR:", cr, "Payload:", payload_size)
        crc = 1  # CRC enabled
        bw_hz = bw * 1000   # Convert bandwidth to Hz
        t_symbol = (2 ** sf) / bw_hz    # Symbol duration
        t_preamble = t_symbol * (8 + 4.25)  # Preamble duration
        h = 0   # Implicit header disabled
        de = 1 if (sf >= 11 and bw == 125) else 0   # Low data rate optimization enabled for SF11 and SF12 with 125kHz BW
        cr_rate = cr / 4.0  # Coding rate
        # Payload Symbol Calculation
        payload_bits = 8 * payload_size - 4 * sf + 28 + 16 * (1 if crc else 0) - 20 * h
        bits_per_symbol = 4 * (sf - 2 * de)
        n_payload = 8 + max(0, int(ceil(payload_bits / bits_per_symbol) * (cr_rate + 4)))
        
        # Payload Duration
        t_payload = t_symbol * n_payload
        
        # Total Time on Air
        t_air = t_preamble + t_payload
        if self.debug:
            print("TOA:", t_air)
        
        return t_air

    def backup_config(self):
        return self.config_parameters

    def get_mac(self):
        return self.MAC

    def set_mesh_mode(self, mesh_mode=False):
        self.mesh_mode = mesh_mode

    def send(self, packet: Packet):
        return None

    def recv(self, focus_time=12):
        return None

    def increase_adaptive_timeout(self):
        random_factor = int.from_bytes(urandom(2), "little") / 2**16
        self.adaptive_timeout = min(self.adaptive_timeout * (1 + random_factor), self.max_timeout)

    def decrease_adaptive_timeout(self, td):
        smoothing_factor = 0.2
        new_timeout = self.adaptive_timeout * (1 - smoothing_factor) + td * smoothing_factor
        self.observed_min_timeout = min(self.observed_min_timeout, td)
        self.adaptive_timeout = max(new_timeout, max(self.min_timeout, self.observed_min_timeout))

    # def send_and_wait_response(self, packet):
    #     focus_time = self.adaptive_timeout
    #     packet_size_sent = len(packet.get_content())
    #     try:
    #         send_success = self.send(packet)
    #         if not send_success:
    #             if self.debug:
    #                 print("SEND_PACKET || Error sending packet")
    #             return None, 0, 0, 0
    #     except Exception as e:
    #         if self.debug:
    #             print("SEND_PACKET || Error sending packet: ", e)
    #         self.increase_adaptive_timeout()
    #         return None, 0, 0, 0

    #     while focus_time > 0:
    #         t0 = time()
    #         received_data = self.recv(focus_time)
    #         td = (time() - t0) / 1000  # Calculate the time difference in seconds
    #         packet_size_received = len(received_data) if received_data else 0

    #         if not received_data:
    #             if self.debug:
    #                 print("WAIT_RESPONSE({}) || No response, FT: {}".format(td, focus_time))
                
    #             self.increase_adaptive_timeout()
    #             return None, packet_size_sent, packet_size_received, td

    #         response_packet = Packet(self.mesh_mode, self.short_mac)
    #         if self.debug:
    #             print("WAIT_RESPONSE({}) at: {}|| source_reply: {}".format(td, self.adaptive_timeout, received_data))
    #             #print("RSSI: ", self.get_rssi(), "SNR: ", self.get_snr())
    #         try:
    #             if response_packet.load(received_data):
    #                 if response_packet.get_source() == packet.get_destination() and response_packet.get_destination() == self.get_mac():
    #                     if len(received_data) > response_packet.HEADER_SIZE + 60:  # Hardcoded for only chunks
    #                         self.decrease_adaptive_timeout(td)
    #                     if response_packet.get_debug_hops():
    #                         response_packet.add_hop(self.name, self.get_rssi(), 0)
    #                     return response_packet, packet_size_sent, packet_size_received, td
    #             else:
    #                 #raise Exception("Corrupted packet")
    #                 return None, packet_size_sent, packet_size_received, td

    #         except Exception as e:
    #             if self.debug:
    #                 print("Connector: ", e)

    #         focus_time = self.adaptive_timeout - td
    #         if focus_time < self.min_timeout:
    #             focus_time = self.min_timeout
    #             if self.debug:
    #                 print("Connector: Can't wait more")
    #             return None, packet_size_sent, packet_size_received, td
    
    def send_and_wait_response(self, packet):
        focus_time = self.adaptive_timeout
        packet_size_sent = len(packet.get_content())
        try:
            send_success = self.send(packet)
            if not send_success:
                error_info = {
                    "type": "SEND_ERROR",
                    "message": "Error sending packet",
                    "focus_time": focus_time,
                    "adaptive_timeout": self.adaptive_timeout,
                }
                if self.debug:
                    print(error_info["message"])
                return error_info, packet_size_sent, 0, 0
        except Exception as e:
            error_info = {
                "type": "EXCEPTION",
                "message": "Exception during send: {}".format(e),
                "focus_time": focus_time,
                "adaptive_timeout": self.adaptive_timeout,
            }
            if self.debug:
                print(error_info["message"])
            self.increase_adaptive_timeout()
            return error_info, packet_size_sent, 0, 0

        while focus_time > 0:
            t0 = time()
            try:
                received_data = self.recv(focus_time)
            except Exception as e:
                error_info = {
                    "type": "EXCEPTION",
                    "message": "Exception during recv: {}".format(e),
                    "focus_time": focus_time,
                    "adaptive_timeout": self.adaptive_timeout,
                }
                if self.debug:
                    print(error_info["message"])
                return error_info, packet_size_sent, 0, 0

            td = (time() - t0) / 1000  # Calculate the time difference in seconds
            packet_size_received = len(received_data) if received_data else 0

            if not received_data:
                error_info = {
                    "type": "TIMEOUT",
                    "message": "No response received",
                    "focus_time": focus_time,
                    "time_difference": td,
                    "adaptive_timeout": self.adaptive_timeout,
                }
                if self.debug:
                    print(error_info["message"])
                self.increase_adaptive_timeout()
                return error_info, packet_size_sent, packet_size_received, td

            response_packet = Packet(self.mesh_mode, self.short_mac)
            if self.debug:
                print("WAIT_RESPONSE({}) at: {}|| source_reply: {}".format(td, self.adaptive_timeout, received_data))
            try:
                if response_packet.load(received_data):
                    if response_packet.get_source() == packet.get_destination() and response_packet.get_destination() == self.get_mac():
                        if len(received_data) > response_packet.HEADER_SIZE + 60:  # Hardcoded for only chunks
                            self.decrease_adaptive_timeout(td)
                        if response_packet.get_debug_hops():
                            response_packet.add_hop(self.name, self.get_rssi(), 0)
                        return response_packet, packet_size_sent, packet_size_received, td
                else:
                    error_info = {
                        "type": "CORRUPTED_PACKET",
                        "message": "Received a corrupted packet",
                    }
                    if self.debug:
                        print(error_info["message"])
                    return error_info, packet_size_sent, packet_size_received, td

            except Exception as e:
                error_info = {
                    "type": "EXCEPTION",
                    "message": "Exception during packet load: {}, data: {}".format(e, received_data),
                }
                if self.debug:
                    print(error_info["message"])
                return error_info, packet_size_sent, packet_size_received, td

            focus_time = self.adaptive_timeout - td
            if focus_time < self.min_timeout:
                focus_time = self.min_timeout
                error_info = {
                    "type": "MIN_TIMEOUT_REACHED",
                    "message": "Minimum timeout reached, can't wait more",
                    "focus_time": focus_time,
                }
                if self.debug:
                    print(error_info["message"])
                return error_info, packet_size_sent, packet_size_received, td

    # This function returns the RSSI of the last received packet
    def get_rssi(self):
        return 0

    # This function returns the SNR of the last received packet
    def get_snr(self):
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
        if self.debug:
            print('SIGNAL STRENGTH', percentage, '%')
        return percentage

    def get_rf_config(self):
        return [self.frequency, self.sf, self.bw, self.cr, self.tx_power]

    def change_rf_config(self, frequency=None, sf=None, bw=None, cr=None, tx_power=None, backup=True):
        if backup:
            self.backup_rf_config()
        try:
            if frequency is not None:
                self.set_frequency(frequency)
            if sf is not None:
                self.set_sf(sf)
            if bw is not None:
                self.set_bw(bw)
            if cr is not None:
                self.set_cr(cr)
            if tx_power is not None:
                self.set_transmission_power(tx_power)
            self.update_timeouts()
            self.adaptive_timeout = self.max_timeout
            return True
        except Exception as e:
            if self.debug:
                print("Error changing RF config: ", e)
            self.restore_rf_config()
            return False

    def backup_rf_config(self):
        self.last_rf_config = [self.frequency, 
                                    self.sf, 
                                    self.bw, 
                                    self.cr, 
                                    self.tx_power]

    def update_rf_params(self, params):
        """
        Updates the connector's RF parameters.
        Override in derived classes if needed.
        """
        self.frequency = params.get("frequency", self.frequency)
        self.sf = params.get("sf", self.sf)
        self.bw = params.get("bw", self.bw)
        self.cr = params.get("cr", self.cr)
        self.tx_power = params.get("tx_power", self.tx_power)
        if self.debug:
            print("Updated RF parameters:", self.get_rf_config())

    def restore_rf_config(self):
        frequency =  self.last_rf_config[0]
        sf = self.last_rf_config[1]
        bw = self.last_rf_config[2] 
        cr = self.last_rf_config[3]
        tx_power = self.last_rf_config[4]
        self.change_rf_config(frequency=frequency, 
                                sf=sf, 
                                bw=bw, 
                                cr=cr, 
                                tx_power=tx_power,
                                backup=False)


    def set_frequency(self, frequency):
        pass

    def set_sf(self, sf):
        pass

    def set_bw(self, bw):
        pass

    def set_cr(self, cr):
        pass

    def set_transmission_power(self, tx_power):
        pass