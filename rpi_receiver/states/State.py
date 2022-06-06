from abc import ABC, abstractmethod
import json
import time

'''
Parent class for every communication state.
'''
class State(ABC):


    REQUEST_DATA_STATE = "REQUEST_DATA_STATE"
    PROCESS_CHUNK_STATE = "PROCESS_CHUNK_STATE"


    @abstractmethod
    def do_action(self, buoy):  # Buoy is the context
        pass

    def write_metadata(self, packet):
        pass
        """
        hops = json.loads(packet.get_part("H"))
        t = time.strftime("%Y-%m-%d_%H:%M:%S")
        line = "{}:{}\n".format(t, hops)
        with open('log_rssi.txt', 'a') as log:
            log.write(line)
            print(line)"""
