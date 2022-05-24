import utils
from File import File
from network import router
from states.State import State
from network.Packet import Packet

'''
This command is the first one to be sent:
    - At the beginning
    - Everytime we want a new File
'''
class RequestDataState(State):


    def __init__(self):
        pass


    def do_action(self, buoy) -> str:
        self.__packet = Packet(mesh_mode = buoy.get_mesh_mode())
        self.__packet.set_destination(buoy.get_mac_address())
        self.__packet.set_part("COMMAND", "request-data-info")
        if buoy.get_mesh():
            self.__packet.enable_mesh()

        utils.logger_debug.debug("Buoy {} RequestDataState command: {}".format(buoy.get_name(), self.__packet.get_content()))
        response_packet = router.send_packet(packet=self.__packet, mesh_mode = buoy.get_mesh_mode())

        if response_packet.is_empty() is False:
            utils.logger_debug.debug("Buoy {} response: {}".format(buoy.get_name(), response_packet.get_content()))
            try:
                self.write_metadata(response_packet)
                filename = response_packet.get_part("FILENAME")
                length = int(response_packet.get_part("LENGTH"))
                new_file = File(filename, length)
                buoy.set_current_file(new_file)
                utils.logger_debug.debug("Buoy {} File {} has been set".format(buoy.get_name(), filename))
                buoy.reset_retransmission_counter(response_packet)
                return State.PROCESS_CHUNK_STATE  # If all went well, continue
                #If message is corrupted...
            except KeyError as e:
                return State.REQUEST_DATA_STATE
        else:
            buoy.count_retransmission()
            return State.REQUEST_DATA_STATE
