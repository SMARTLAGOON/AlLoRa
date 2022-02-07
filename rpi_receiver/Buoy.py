import json
import os
import pickle
import time
from threading import Thread

import requests

from File import File
from states.ProcessChunkState import ProcessChunkState
from states.RequestDataState import RequestDataState

'''
This class helps to handle senders (buoys) in a handy way.
It mounts a basic State pattern helping with communication protocol, also saves its state just in case of a blackout or whatever. 
'''
class Buoy:


    REQUEST_DATA_STATE = RequestDataState()
    PROCESS_CHUNK_STATE = ProcessChunkState()


    def __init__(self, name: str, coordinates: tuple, mac_address: str):
        self.__name = name
        self.__coordinates = coordinates #(lat, lon, alt)
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

    def sync_remote(self, endpoint: str):
        def sync(buoy, endpoint: str):
            while (True):
                try:
                    # List directory
                    file_names = os.listdir('./{}'.format(self.__mac_address))
                    # Open each file
                    for f in file_names:
                        print(f)
                        with open('./{}/{}'.format(self.__mac_address, f), 'r') as fp:
                            file_content = json.loads(fp.read())
                            #This is the Sensingtools format
                            content_to_upload = list()
                            for k, v in file_content.items():
                                content_to_upload.append({"name": self.__name,
                                                      "lat": self.__coordinates[0],
                                                      "lon": self.__coordinates[1],
                                                      "alt": self.__coordinates[2],
                                                      "sensor_type": k,
                                                      "value": v,
                                                      "timestamp": buoy.__current_file.get_timestamp()})

                            print("ENVIANDO", content_to_upload)
                            status_code = 0
                            # Not-to-lose-even-one approach
                            while status_code != 200:
                                try:
                                    response = requests.post(url=endpoint, json= content_to_upload)
                                    status_code = response.status_code
                                except Exception as e:
                                    print(e)
                                finally:
                                    time.sleep(5) #For not to overload server
                            os.remove('./{}/{}'.format(self.__mac_address, f))
                except FileNotFoundError as e:
                    pass

        thread = Thread(target=sync, args=(self, endpoint,))
        thread.start()


