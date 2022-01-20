from File import File
from states.State import State
from utils import send_command


class RequestDataState(State):


    def __init__(self):
        self.__command = "MAC:::{};;;COMMAND:::request-data-info"


    def do_action(self, buoy) -> str:
        mac_address = buoy.get_mac_address()
        response = send_command(self.__command.format(mac_address), mac_address)
        if response != "":
            print("rds response", response)
            filename = response.split(";;;")[2].split(":::")[1]
            length = int(response.split(";;;")[1].split(":::")[1])
            new_file = File(filename, length)
            buoy.set_current_file(new_file)
            print("file set, now changing state")
            return State.PROCESS_CHUNK_STATE  # Si fue bien, continuamos
        else:
            return State.REQUEST_DATA_STATE  # Repetimos proceso si salió mal (it may bring the next File because sender buoy is not taking note whether the last was received or not)