from AlLoRa.Packet import Packet
import gc
try:
    from utime import sleep, ticks_ms as time
    from uos import urandom
except:
    from time import sleep, time
    from os import urandom

class Connector:
    MAX_LENGTH_MESSAGE = 255

    def __init__(self):
        self.MAC = "00000000"

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

    def send_and_wait_response(self, packet):
        packet.set_source(self.get_mac())  # Adding mac address to packet
        focus_time = self.adaptive_timeout
        send_success = self.send(packet)
        #if not send_success:
            #return None

        while focus_time > 0:
            t0 = time()
            received_data = self.recv(focus_time)
            td = (time() - t0)/1000
            if not received_data:
                random_factor = int.from_bytes(urandom(2), "little") / 2**16
                self.adaptive_timeout = min(self.adaptive_timeout * (1 + random_factor),
                                        self.max_timeout) #random exponential backoff.
                gc.collect()
                return None
            response_packet = Packet(self.mesh_mode)
            if self.debug:
                self.signal_estimation()
                print("WAIT_RESPONSE({}) || source_reply: {}".format(self.adaptive_timeout, received_data))
            try:
                response_packet.load(received_data)
                if response_packet.get_source() == packet.get_destination() and response_packet.get_destination() == self.get_mac():
                    if len(received_data) > response_packet.HEADER_SIZE + 60:	# Hardcoded for only chunks
                        self.adaptive_timeout = max(self.adaptive_timeout * 0.8 + td * 0.21, self.min_timeout)
                    if response_packet.get_debug_hops():
                        response_packet.add_hop(self.name, self.get_rssi(), 0)
                    if response_packet.get_change_sf():
                        new_sf = int(response_packet.get_payload().decode().split('"')[1])
                        if self.debug:
                            print("OK and changing sf: ", new_sf)
                        self.set_sf(new_sf)
                    gc.collect()
                    return response_packet
            except Exception as e:
                if self.debug:
                    print("Corrupted packet received", e, received_data)
            focus_time = self.adaptive_timeout - td

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
        if self.debug:
            print('SIGNAL STRENGTH', percentage, '%')
        return percentage
