from AlLoRa.Nodes.Receiver import Receiver

class Gateway(Receiver):

    def __init__(self, connector = None, config_file = "LoRa.json", debug_hops = False, 
                    NEXT_ACTION_TIME_SLEEP = 0.1, 
                    TIME_PER_ENDPOINT = 10):
        super().__init__(connector,  config_file, debug_hops = debug_hops,
                            NEXT_ACTION_TIME_SLEEP = NEXT_ACTION_TIME_SLEEP)
        self.TIME_PER_ENDPOINT = TIME_PER_ENDPOINT
    
    
    def set_digital_endpoints(self, digital_endpoints):
        self.digital_endpoints = digital_endpoints

    def check_digital_endpoints(self, print_file_content=False):
        while True:
            for digital_endpoint in self.digital_endpoints:
                file = self.listen_to_endpoint(digital_endpoint, self.TIME_PER_ENDPOINT, return_file=print_file_content)
                if file and print_file_content:
                    print(file.get_content())