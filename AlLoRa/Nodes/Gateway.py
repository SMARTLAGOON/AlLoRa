from AlLoRa.Nodes.Requester import Requester
from AlLoRa.Digital_Endpoint import Digital_Endpoint
from AlLoRa.utils.time_utils import current_time_ms as time, sleep
from AlLoRa.utils.debug_utils import print
from AlLoRa.utils.os_utils import os
from os import urandom
from AlLoRa.utils.json_utils import json
from json import loads, dumps

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

        self.status["Status"] = "WAIT"  # Status of the requester
        self.status["RSSI"] = "-" # Signal strength
        self.status["SNR"] = "-"   # Signal to Noise Ratio
        self.status["Chunk"] = "-"  # Chunk being received
        self.status["File"] = "-"   # File name being received
        self.status["SMAC"] = "-"   # Source MAC
        # Digital Endpoint file_reception_info
        self.status["Digital_Endpoints"] = {ep.get_mac_address(): ep.file_reception_info for ep in self.digital_endpoints}
    
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
                        print("Node {} ({}) added with frequency {}s and listening time {}s.".format(active_node.get_name(), active_node.get_mac_address(), active_node.asking_frequency, active_node.listening_time))
            return len(self.digital_endpoints)
        except Exception as e:
            if self.debug:
                print("Could not load nodes from file: {}, error: {}".format(path, e))
            return False

    def check_digital_endpoints(self, print_file_content=False, save_files=False):
        print("Listening to {} endpoints!".format(len(self.digital_endpoints)))
        next_check_times = {ep.get_mac_address(): 0 for ep in self.digital_endpoints}

        while True:
            current_time = time()   # Current time in miliseconds
            for ep in sorted(self.digital_endpoints, key=lambda x: next_check_times[x.get_mac_address()]):
                if current_time >= next_check_times[ep.get_mac_address()]:
                    try:
                        # Initial listening session for the endpoint
                        if self.debug:
                            print("Listening to endpoint {} ({}) for {}s".format(ep.get_name(), ep.get_mac_address(), ep.listening_time))

                        self.listen_to_endpoint(ep, ep.listening_time,
                                                print_file=print_file_content, save_file=save_files)
                        
                        self.update_subscribers(ep)
                        # Check if additional time is needed due to incomplete file transfer
                        if ep.get_current_file() is not None:
                            if ep.lock_on_file_receive and ep.get_current_file().get_missing_chunks():
                                # Extend the listening for one additional period if there are missing chunks
                                if self.debug:
                                    print("Listening to endpoint {} ({}) for {}s due to missing chunks".format(ep.get_name(), ep.get_mac_address(), ep.max_listen_time_when_locked))
                                self.listen_to_endpoint(ep, ep.max_listen_time_when_locked,
                                                        print_file=print_file_content, save_file=save_files)
                                self.update_subscribers(ep)

                    except Exception as e:
                        if self.debug:
                            print("Error listening to endpoint {} ({}): {}".format(ep.get_name(), ep.get_mac_address(), e))
                    finally:
                        # Reschedule next check regardless of success or error
                        next_check_times[ep.get_mac_address()] = time() + ep.asking_frequency

                sleep(self.NEXT_ACTION_TIME_SLEEP)

    def update_subscribers(self, digital_endpoint):
        self.status["Digital_Endpoints"][digital_endpoint.get_mac_address()] = digital_endpoint.file_reception_info
        self.notify_subscribers()


                   
