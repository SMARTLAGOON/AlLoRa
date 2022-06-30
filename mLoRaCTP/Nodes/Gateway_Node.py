from mLoRaCTP.Nodes.Receiver_Node import mLoRaCTP_Receiver

class mLoRaCTP_Gateway(mLoRaCTP_Receiver):

    def __init__(self, mesh_mode = False, debug_hops = False, connector = None, 
                    NEXT_ACTION_TIME_SLEEP = 0.1, 
                    TIME_PER__ENDPOINT = 10):
        mLoRaCTP_Receiver.__init__(self, mesh_mode, debug_hops, connector = connector, 
                                    NEXT_ACTION_TIME_SLEEP = NEXT_ACTION_TIME_SLEEP)
        self.TIME_PER_ENDPOINT = TIME_PER__ENDPOINT
    
    def set_digital_endpoints(self, digital_endpoints):
        self.digital_endpoints = digital_endpoints

    def check_digital_endpoints(self):
        while True:
            for digital_endpoint in self.digital_endpoints:
                self.listen_to_endpoint(digital_endpoint, self.TIME_PER_ENDPOINT)