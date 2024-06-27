from AlLoRa.Packet import Packet
import gc
try:
    from utime import sleep, sleep_ms, ticks_ms as time
    from uos import urandom
except:
    from time import sleep, time
    from os import urandom

class Connector:
    MAX_LENGTH_MESSAGE = 255

    def __init__(self):
        self.MAC = "00000000"
        self.observed_min_timeout = float('inf')

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
            self.frequency = self.config_parameters.get('frequency', 868)
            self.sf = self.config_parameters.get('sf', 7)
            self.mesh_mode = self.config_parameters.get('mesh_mode', False)
            self.debug = self.config_parameters.get('debug', False)
            self.min_timeout = self.config_parameters.get('min_timeout', 0.5)
            self.max_timeout = self.config_parameters.get('max_timeout', 6)
            
            self.adaptive_timeout = self.min_timeout
            self.backup_timeout = self.adaptive_timeout
            self.sf_backup = self.sf
        else:
            if self.debug:
                print("Error: No config parameters")

    def backup_config(self):
        return self.config_parameters

    def get_mac(self):
        return self.MAC

    def set_sf(self, sf):
        pass

    def backup_sf(self):
        self.sf_backup = self.sf

    def restore_sf(self):
        self.set_sf(self.sf_backup)

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

    def send_and_wait_response(self, packet):
        packet.set_source(self.get_mac())  # Adding Mac address to packet
        focus_time = self.adaptive_timeout
        packet_size_sent = len(packet.get_content())
        send_success = self.send(packet)
        if not send_success:
            if self.debug:
                print("SEND_PACKET || Error sending packet")
            return None, 0, 0, 0

        while focus_time > 0:
            t0 = time()
            received_data = self.recv(focus_time)
            td = (time() - t0) / 1000  # Calculate the time difference in seconds
            packet_size_received = len(received_data) if received_data else 0

            if not received_data:
                if self.debug:
                    print("WAIT_RESPONSE({}) || No response, FT: {}".format(td, focus_time))
                
                self.increase_adaptive_timeout()
                return None, packet_size_sent, packet_size_received, td

            response_packet = Packet(self.mesh_mode)
            if self.debug:
                print("WAIT_RESPONSE({}) at: {}|| source_reply: {}".format(td, self.adaptive_timeout, received_data))
                #print("RSSI: ", self.get_rssi(), "SNR: ", self.get_snr())
            try:
                if response_packet.load(received_data):
                    if response_packet.get_source() == packet.get_destination() and response_packet.get_destination() == self.get_mac():
                        if len(received_data) > response_packet.HEADER_SIZE + 60:  # Hardcoded for only chunks
                            self.decrease_adaptive_timeout(td)
                        if response_packet.get_debug_hops():
                            response_packet.add_hop(self.name, self.get_rssi(), 0)
                        if response_packet.get_change_sf():
                            new_sf = int(response_packet.get_payload().decode().split('"')[1])
                            if self.debug:
                                print("OK and changing sf: ", new_sf)
                            self.set_sf(new_sf)
                        return response_packet, packet_size_sent, packet_size_received, td
                else:
                    raise Exception("Corrupted packet")

            except Exception as e:
                if self.debug:
                    print("Connector: ", e, received_data)

            focus_time = self.adaptive_timeout - td
            if focus_time < self.min_timeout:
                focus_time = self.min_timeout
                if self.debug:
                    print("Connector: Can't wait more")
                return None, packet_size_sent, packet_size_received, td

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
