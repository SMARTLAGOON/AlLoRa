import utils
from lora_ctp.File import File
from lora_ctp import ctp_node
from states.State import State
from lora_ctp.Packet import Packet

'''
This command is the first one to be sent:
    - At the beginning
    - Everytime we want a new File
'''
class RequestDataState(State):

    def __init__(self):
        pass

    def do_action(self, buoy) -> str:

        metadata, hop = buoy.lora_node.ask_metadata(buoy.get_mac_address(), buoy.get_mesh())
        if metadata:
            length = metadata[0]
            filename = metadata[1]
            new_file = File(filename, length)
            buoy.set_current_file(new_file)
            buoy.reset_retransmission_counter(hop)
            utils.logger_debug.debug("Buoy {} File {} has been set".format(buoy.get_name(), filename))
            return State.PROCESS_CHUNK_STATE  # If all went well, continue
        else:
            buoy.count_retransmission()
            return State.REQUEST_DATA_STATE
