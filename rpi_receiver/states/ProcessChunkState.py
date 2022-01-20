from states.State import State
from utils import send_command


class ProcessChunkState(State):


    def __init__(self):
        self.__command = "MAC:::{};;;COMMAND:::chunk-{}"


    def do_action(self, buoy) -> str:
        mac_address = buoy.get_mac_address()
        file = buoy.get_current_file()
        print("process chunk state")
        print("missing chunks", file.get_missing_chunks())
        if len(file.get_missing_chunks()) > 0: #Si siguen habiendo chunks...
            next_chunk = file.get_missing_chunks()[0]  # Podría ser cualquiera, pero cogemos por orden
            print("pcs", self.__command.format(mac_address, next_chunk))
            response = send_command(self.__command.format(mac_address, next_chunk), mac_address)
            print("pcs response", response)
            if response != "":
                new_chunk = response.split(';;;')[1].split(':::')[1].encode()
                file.add_chunk(next_chunk, new_chunk)
            return State.PROCESS_CHUNK_STATE #Tanto si ha salido bien como si ha salido mal, seguimos en fase de obtener chunks
        else: #Si no los hay...
            print(file.get_content())
            return State.REQUEST_DATA_STATE #Si el fichero ya no tiene más chunks, hay que volver a iniciar el proceso