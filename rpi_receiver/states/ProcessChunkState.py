import utils
from lora_ctp import ctp_node
from states.State import State
from lora_ctp.Packet import Packet

'''
This command is sent:
    - As a first chunk request after the first RequestDataState was sent and replied,
in fact the returned data is needed to make up the ProcessChunkState command.

    - After a previous ProcessChunkState, until the last chunk of the current File is received.
'''


class ProcessChunkState(State):

    def __init__(self):
        pass

    def do_action(self, buoy) -> str:
        file = buoy.get_current_file()
        utils.logger_debug.debug("Buoy {} Missing chunks: {}".format(buoy.get_name(), file.get_missing_chunks()))

        # While there are chunks...
        if len(file.get_missing_chunks()) > 0:
            # It may be any, but we keep an order, so not.
            next_chunk = file.get_missing_chunks()[0]
            data, hop = buoy.lora_node.ask_data(buoy.get_mac_address(), buoy.get_mesh(), next_chunk)
            if data:
                file.add_chunk(next_chunk, data)
                buoy.reset_retransmission_counter(hop) #response_packet
            else:
                buoy.count_retransmission()

        if len(file.get_missing_chunks()) <= 0:
            return State.REQUEST_DATA_STATE

        # While chunks are left.
        return State.PROCESS_CHUNK_STATE
