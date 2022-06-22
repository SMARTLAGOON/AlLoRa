from lora_ctp.receiver_node import LoRa_CTP_Receiver

class LoRa_CTP_Gateway(LoRa_CTP_Receiver):

    def __init__(self, mesh_mode = False, debug_hops = False, adapter = None, 
                    NEXT_ACTION_TIME_SLEEP = 0.1, 
                    TIME_PER_BUOY = 10):
        LoRa_CTP_Receiver.__init__(self, mesh_mode, debug_hops, adapter = adapter)

        self.NEXT_ACTION_TIME_SLEEP = NEXT_ACTION_TIME_SLEEP
        self.TIME_PER_BUOY = TIME_PER_BUOY
    
    def set_datasources(self, datasources):
        self.datasources = datasources

    def check_datasources(self):
        while True:
            for datasource in self.datasources:
                self.listen_datasource(datasource, self.TIME_PER_BUOY)

if __name__ == "__main__":
    from adapters.Wifi_adapter import WiFi_adapter
    adapter = WiFi_adapter(1,2,3,4,5,6)
    gateway = LoRa_CTP_Gateway(mesh_mode = True, debug_hops = False, adapter = adapter, 
                                NEXT_ACTION_TIME_SLEEP = 0.1, 
                                TIME_PER_BUOY = 10)
    
    metadata, hop = gateway.ask_metadata("12345678", True)