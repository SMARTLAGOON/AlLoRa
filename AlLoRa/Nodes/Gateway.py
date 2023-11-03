try:
    from uos import urandom
    from ujson import loads, dumps
except:
    from os import urandom
    from json import loads, dumps

from AlLoRa.Nodes.Requester import Requester
from AlLoRa.Digital_Endpoint import Digital_Endpoint

class Gateway(Requester):

    def __init__(self, connector = None, config_file = "LoRa.json", debug_hops = False, 
                    NEXT_ACTION_TIME_SLEEP = 0.1, 
                    TIME_PER_ENDPOINT = 10, nodes_file = "Nodes.json"):
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

        super().__init__(connector,  config_file, debug_hops = debug_hops,
                            NEXT_ACTION_TIME_SLEEP = NEXT_ACTION_TIME_SLEEP)
        self.TIME_PER_ENDPOINT = TIME_PER_ENDPOINT
        self.nodes_file = nodes_file
        self.digital_endpoints = []
        self.add_digital_endpoints(self.nodes_file)
    
    def set_digital_endpoints(self, digital_endpoints):
        self.digital_endpoints = digital_endpoints

    def add_digital_endpoints(self, path):
        try:
            count_nodes = 0
            with open(path, "r") as f:
                nodes_config = loads(f.read())
            for node in nodes_config:
                retries = None
                try:
                    retries = node['MAX_RETRIES_BEFORE_MESH']
                except:
                    retries = 10
                if node['active']:
                    active_node = Digital_Endpoint(node)
                    self.digital_endpoints.append(active_node)                                            
                    count_nodes += 1
                    if self.debug:
                        print("Node {} added!".format(active_node.mac_address))
            return count_nodes
        except:
            print("Could not load nodes from file: {}, please set manually or add missing file".format(path))
            return False

    def check_digital_endpoints(self, print_file_content=False, save_files=False):
        print("Listening to {} endpoints!".format(len(self.digital_endpoints)))
        while True:
            for digital_endpoint in self.digital_endpoints:
                try:
                    self.listen_to_endpoint(digital_endpoint, digital_endpoint.listening_time, 
                                        print_file=print_file_content, save_file=save_files)
                except Exception as e:
                    if self.debug:
                        print("Error listening to endpoint: {}".format(e))

                   
