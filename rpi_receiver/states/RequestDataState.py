from File import File
from states.State import State
from utils import send_command

'''
This command is the first one to be sent:
    - At the beginning
    - Everytime we want a new File
'''
class RequestDataState(State):


    def __init__(self):
        self.__command = "MAC:::{};;;COMMAND:::request-data-info"


    def do_action(self, buoy) -> str:
        mac_address = buoy.get_mac_address()
        response = send_command(self.__command.format(mac_address), mac_address)
        if response != "":
            #TODO Implement formal logging system
            print("rds response", response)
            filename = response.split(";;;")[2].split(":::")[1]
            length = int(response.split(";;;")[1].split(":::")[1])
            new_file = File(filename, length)
            buoy.set_current_file(new_file)
            print("file set, now changing state")
            return State.PROCESS_CHUNK_STATE  # If all went well, continue
        else:
            return State.REQUEST_DATA_STATE  # If not, the process is repeated (it may bring the next File because sender buoy is not taking note whether the last was received or not, because it is moking up datalogger)