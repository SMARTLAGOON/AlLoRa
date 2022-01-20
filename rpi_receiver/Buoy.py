import os
import pickle

from File import File
from states.ProcessChunkState import ProcessChunkState
from states.RequestDataState import RequestDataState


class Buoy:


    REQUEST_DATA_STATE = RequestDataState()
    PROCESS_CHUNK_STATE = ProcessChunkState()


    def __init__(self, mac_address: str):
        self.__mac_address = mac_address
        self.__next_state = RequestDataState()
        self.__current_file = None


    def get_mac_address(self):
        return self.__mac_address


    def set_current_file(self, file: File):
        self.__current_file = file
        self.__backup()


    def get_current_file(self):
        return self.__current_file


    def do_next_action(self):
        self.__next_state = self.__getattribute__(self.__next_state.do_action(self))
        self.__backup()


    def __backup(self):

        try:
            os.mkdir('application_backup')
        except Exception as e:
            pass
        with open('application_backup/buoy_{}.pickle.bak'.format(self.__mac_address), 'wb') as fp:
            pickle.dump(self, fp)

        if self.__current_file is not None and len(self.__current_file.get_missing_chunks()) <= 0:
            try:
                os.mkdir(self.__mac_address)
            except Exception as e:
                pass
            with open('./{}/{}'.format(self.__mac_address, self.__current_file.get_name()), 'wb') as fp:
                fp.write(self.__current_file.get_content().encode('utf-8'))