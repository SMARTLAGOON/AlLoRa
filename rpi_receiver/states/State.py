from abc import ABC, abstractmethod


class State(ABC):


    REQUEST_DATA_STATE = "REQUEST_DATA_STATE"
    PROCESS_CHUNK_STATE = "PROCESS_CHUNK_STATE"


    @abstractmethod
    def do_action(self, buoy):  # Buoy es el Context
        pass