from time import time, sleep
try:
    from uos import urandom
    from ujson import loads, dumps
except:
    from os import urandom
    from json import loads, dumps

from AlLoRa.Nodes.Requester import Requester
from AlLoRa.Digital_Endpoint import Digital_Endpoint

class Gateway(Requester):

    def __init__(self, connector=None, config_file="LoRa.json", debug_hops=False, 
                    NEXT_ACTION_TIME_SLEEP=0.1, nodes_file="Nodes.json"):
        #JSON Example:
        # {
        #     "name": "G",
        #     "frequency": 868,
        #     "sf": 7,
        #     "mesh_mode": false,
        #     "debug": false,
        #     "min_timeout": 0.5,
        #     "max_timeout": 6,
        #     "result_path": "Results/",
        #     "nodes_file": "Nodes.json",
        #     "time_per_endpoint": 10
        # }

        super().__init__(connector,  config_file, debug_hops=debug_hops,
                            NEXT_ACTION_TIME_SLEEP=NEXT_ACTION_TIME_SLEEP)
        self.nodes_file = nodes_file
        self.digital_endpoints = []
        self.add_digital_endpoints(self.nodes_file)
    
    def set_digital_endpoints(self, digital_endpoints):
        self.digital_endpoints = digital_endpoints

    def add_digital_endpoints(self, path):
        try:
            with open(path, "r") as f:
                nodes_config = loads(f.read())
            for node in nodes_config:
                if node['active']:
                    active_node = Digital_Endpoint(node)
                    self.digital_endpoints.append(active_node)                                            
                    if self.debug:
                        print("Node {} added with frequency {}s and listening time {}s.".format(active_node.get_mac_address(), active_node.asking_frequency, active_node.listening_time))
            return len(self.digital_endpoints)
        except Exception as e:
            print("Could not load nodes from file: {}, error: {}".format(path, e))
            return False

    def check_digital_endpoints(self, print_file_content=False, save_files=False):
        print("Listening to {} endpoints!".format(len(self.digital_endpoints)))
        next_check_times = {ep.get_mac_address(): 0 for ep in self.digital_endpoints}

        while True:
            current_time = time()
            for ep in self.digital_endpoints:
                if current_time >= next_check_times[ep.get_mac_address()]:
                    try:
                        if self.debug:
                            print("Listening to endpoint {} for {} seconds".format(ep.get_mac_address(), ep.listening_time))
                        self.listen_to_endpoint(ep, ep.listening_time, 
                                                print_file=print_file_content, save_file=save_files)
                        next_check_times[ep.get_mac_address()] = current_time + ep.asking_frequency
                        if ep.lock_on_file_receive and len(ep.get_current_file().get_missing_chunks()) > 0:
                            while len(ep.get_current_file().get_missing_chunks()) > 0 and (time() - current_time < ep.listening_time):
                                self.listen_to_endpoint(ep, ep.listening_time, 
                                                        print_file=print_file_content, save_file=save_files)
                    except Exception as e:
                        if self.debug:
                            print("Error listening to endpoint {}: {}".format(ep.get_mac_address(), e))
                else:
                    if self.debug:
                        print("Waiting for endpoint {} to be checked.".format(ep.get_mac_address()))
                    sleep(self.NEXT_ACTION_TIME_SLEEP)
            sleep(self.NEXT_ACTION_TIME_SLEEP)

                   
