from m3LoRaCTP.Nodes.Receiver_Node import m3LoRaCTP_Receiver

class m3LoRaCTP_Gateway(m3LoRaCTP_Receiver):

    def __init__(self, mesh_mode = False, debug_hops = False, connector = None, 
                    NEXT_ACTION_TIME_SLEEP = 0.1, 
                    TIME_PER_ENDPOINT = 10):
        m3LoRaCTP_Receiver.__init__(self, mesh_mode, debug_hops, connector = connector, 
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