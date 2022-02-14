import utils
from states.State import State
from utils import send_command

'''
This command is sent:
    - As a first chunk request after the first RequestDataState was sent and replied, 
in fact the returned data is needed to make up the ProcessChunkState command.

    - After a previous ProcessChunkState, until the last chunk of the current File is received.
'''
class ProcessChunkState(State):


    def __init__(self):
        self.__command = "MAC:::{};;;COMMAND:::chunk-{}"


    def do_action(self, buoy) -> str:
        utils.logger_debug.debug("Buoy {} ProcessChunkState command: {}".format(buoy.get_name(), self.__command))
        mac_address = buoy.get_mac_address()
        
        file = buoy.get_current_file()
        utils.logger_debug.debug("Buoy {} Missing chunks: {}".format(buoy.get_name(), file.get_missing_chunks()))

        # While there are chunks...
        if len(file.get_missing_chunks()) > 0:
            # It may be any, but we keep an order, so not.
            next_chunk = file.get_missing_chunks()[0]
            utils.logger_debug.debug("Buoy {} Next chunk command: {}".format(buoy.get_name(), self.__command.format(mac_address, next_chunk)))
            response = send_command(command=self.__command.format(mac_address, next_chunk), buoy=buoy)
            utils.logger_debug.debug("Buoy {} Response: {}".format(buoy.get_name(), response))
            if response != "":
                new_chunk = response.split(';;;')[1].split(':::')[1].encode()
                file.add_chunk(next_chunk, new_chunk)
                
            # If this chunk was the last one, the cycle is reset
            if len(file.get_missing_chunks()) <= 0:
                return State.REQUEST_DATA_STATE
            
            # While chunks are left.
            return State.PROCESS_CHUNK_STATE