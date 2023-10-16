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
                    self.digital_endpoints.append(Digital_Endpoint(name=node['name'], 
                                                                mac_address = node['mac_address'], 
                                                                active = node['active'], 
                                                                sleep_mesh=node['sleep_mesh'],
                                                                MAX_RETRANSMISSIONS_BEFORE_MESH=retries))
                                                                
                    count_nodes += 1
            return count_nodes
        except:
            print("Could not load nodes from file: {}, please set manually or add missing file".format(path))
            return False

    def check_digital_endpoints(self, print_file_content=False, save_files=False):
        print("Listening to {} endpoints!".format(len(self.digital_endpoints)))
        while True:
            for digital_endpoint in self.digital_endpoints:
                self.listen_to_endpoint(digital_endpoint, self.TIME_PER_ENDPOINT, 
                                        print_file=print_file_content, save_file=save_files)

                   