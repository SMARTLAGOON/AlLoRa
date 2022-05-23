import utils
from network import router
from states.State import State
from network.Packet import Packet

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
        self.__packet = Packet(mesh_mode = buoy.get_mesh_mode())
        self.__packet.set_destination(buoy.get_mac_address())
        self.__packet.set_part("COMMAND")
        if buoy.get_mesh():
            self.__packet.enable_mesh()

        file = buoy.get_current_file()
        utils.logger_debug.debug("Buoy {} Missing chunks: {}".format(buoy.get_name(), file.get_missing_chunks()))

        # While there are chunks...
        if len(file.get_missing_chunks()) > 0:
            # It may be any, but we keep an order, so not.
            next_chunk = file.get_missing_chunks()[0]
            self.__packet.fill_part("COMMAND", "chunk-{}".format(next_chunk))
            utils.logger_debug.debug(
                "Buoy {} Next chunk command: {}".format(buoy.get_name(), self.__packet.get_content()))

            response_packet = router.send_packet(packet=self.__packet, mesh_mode = buoy.get_mesh_mode())
            utils.logger_debug.debug("Buoy {} Response: {}".format(buoy.get_name(), response_packet.get_content()))

            if response_packet.is_empty() is False:
                try:
                    self.write_metadata(response_packet)
                    new_chunk = response_packet.get_part("CHUNK").encode()
                    file.add_chunk(next_chunk, new_chunk)
                    buoy.reset_retransmission_counter()
                    #If corrupted message..
                except KeyError as e:
                    pass
            else:
                buoy.count_retransmission()

            # If this chunk was the last one, the cycle is reset
            if len(file.get_missing_chunks()) <= 0:
                return State.REQUEST_DATA_STATE

            # While chunks are left.
            return State.PROCESS_CHUNK_STATE
