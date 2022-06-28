from mLoRaCTP.Nodes.Receiver_Node import mLoRaCTP_Receiver

class mLoRaCTP_Gateway(mLoRaCTP_Receiver):

    def __init__(self, mesh_mode = False, debug_hops = False, connector = None, 
                    NEXT_ACTION_TIME_SLEEP = 0.1, 
                    TIME_PER_BUOY = 10):
        mLoRaCTP_Receiver.__init__(self, mesh_mode, debug_hops, connector = connector)

        self.NEXT_ACTION_TIME_SLEEP = NEXT_ACTION_TIME_SLEEP
        self.TIME_PER_BUOY = TIME_PER_BUOY
    
    def set_datasources(self, datasources):
        self.datasources = datasources

    def check_datasources(self):
        while True:
            for datasource in self.datasources:
                self.listen_datasource(datasource, self.TIME_PER_BUOY)