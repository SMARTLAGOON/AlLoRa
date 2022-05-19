import json
import os
import pickle
import time
from json.decoder import JSONDecodeError
from multiprocessing.context import Process
import requests
import utils
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


    def __init__(self, name: str, coordinates: tuple, mac_address: str, uploading_endpoint: str):
        self.__name = name
        self.__coordinates = coordinates #(lat, lon, alt)
        self.__mac_address = mac_address
        self.__uploading_endpoint = uploading_endpoint

        self.__next_state = RequestDataState()
        self.__current_file = None

        self.__mesh = False
        self.__retransmission_counter = 0
        self.__MAX_RETRANSMISSIONS_BEFORE_MESH = 5  # MRBM
        self.__mesh_t0 = None
        self.__MAX_MESH_MINUTES = 60                # MMM (minutes)


    def get_name(self):
        return self.__name

    def get_mac_address(self):
        return self.__mac_address

    def get_mesh(self):
        return self.__mesh

    def enable_mesh(self):
        self.__mesh = True
        self.__mesh_t0 = time.time()

    def disable_mesh(self):
        self.__mesh = False
        self.__mesh_t0 = None
        self.__retransmission_counter = 0

    def check_mesh(self):
        if self.__mesh:
            if (time.time() - self.mesh_t0) / 60 > self.__MAX_MESH_MINUTES:
                self.disable_mesh()

    def count_retransmission(self):
        print("BUOY {}: retransmission + 1".format(self.__name))
        self.__retransmission_counter += 1
        if self.__retransmission_counter >= self.__MAX_RETRANSMISSIONS_BEFORE_MESH:
            print("BUOY {}: ENABLING MESH".format(self.__name))
            self.enable_mesh()

    def set_current_file(self, file: File):
        self.__current_file = file
        self.__backup()

    def get_current_file(self):
        return self.__current_file


    def do_next_action(self):
        self.__next_state = self.__getattribute__(self.__next_state.do_action(self))
        self.check_mesh()
        self.__backup()


    '''
    This function saves the state of the application serializing itself.

    It also saves the data received from buoys in their specific folders.
    '''
    def __backup(self):
        utils.logger_debug.debug("Buoy {} Backing up".format(self.__name))
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


            #TODO Remove the timestamp in filename, this is a temporal solution until datalogger arrives
            def create_filename():
                timestamp = self.__current_file.get_timestamp()
                original_filename = self.__current_file.get_name()
                new_filename = "{}-{}".format(timestamp, original_filename)

                directory = './{}'.format(self.__mac_address)
                filenames = os.listdir(directory)

                for f in filenames:
                    existing_original_filename = f.split("-")[1]
                    if original_filename == existing_original_filename:
                        return f
                return new_filename

            with open('./{}/{}'.format(self.__mac_address, create_filename()), 'wb') as fp:
                fp.write(self.__current_file.get_content().encode('utf-8'))
            utils.logger_info.info("Buoy {} Saved file {} containing {}".format(self.__name, self.__current_file.get_name(), self.__current_file.get_content().encode('utf-8')))


    '''
    This function looks for content in a constant loop.
    '''
    def sync_remote(self):

        def sync(buoy_mac_address: str):
            current_buoy = None
            for buoy in utils.load_buoys_json():
                if buoy['mac_address'] == buoy_mac_address:
                    current_buoy = buoy
                    break

            if current_buoy is None:
                utils.logger_error.error("Buoy {} Mac address was not found in buoys json")
                return

            while (True):
                try:
                    # List directory
                    directory = './{}'.format(buoy_mac_address)
                    utils.logger_debug.debug("Buoy {} Listing directory {}".format(current_buoy['name'], directory))
                    file_names = os.listdir(directory)
                    # Open each file
                    for f in file_names:
                        file_timestamp = int(f.split("-")[0]) #TODO Remove, this is a temporal solution until datalogger arrives
                        with open('./{}/{}'.format(current_buoy['mac_address'], f), 'r') as fp:
                            # JSONDecodeError happens when the filepointer returns None, It has been observed that when read
                            # ... a couple of seconds after, it is get filled so, seems to be an OS sync latency.
                            # ... So, capturing the exception JSONDecodeError and trying again might be enough
                            utils.logger_debug.debug("Buoy {} Reading content of {}".format(current_buoy['name'], f))

                            #Read the content
                            file_content = json.loads(fp.read())

                            #This is the Sensingtools format.
                            content_to_upload = list()
                            for k, v in file_content.items():
                                content_to_upload.append({"name": current_buoy['name'],
                                                          "lat": current_buoy['lat'],
                                                          "lon": current_buoy['lon'],
                                                          "alt": current_buoy['alt'],
                                                          "sensor_type": k,
                                                          "value": v,
                                                          "timestamp": file_timestamp})

                            #We have made an array with each measure from the JSON file.
                            utils.logger_info.info("Buoy {} Content of file {} to be synced: {}".format(current_buoy['name'], f, content_to_upload))
                            status_code = 0
                            retries = utils.SYNC_REMOTE_FILE_SENDING_MAX_RETRIES
                            while status_code != 200 and retries > 0:
                                utils.logger_info.info("Buoy {} {} remaining retries for file {}".format(current_buoy['name'], retries, f))
                                try:
                                    #The JSON Array is sent
                                    response = requests.post(url=current_buoy['uploading_endpoint'], json=content_to_upload)
                                    status_code = response.status_code
                                except Exception as e:
                                    utils.logger_error.error("Buoy {} Exception: {}".format(current_buoy['name'], e))
                                finally:
                                    retries -= 1
                                    time.sleep(utils.SYNC_REMOTE_FILE_SENDING_TIME_SLEEP) # Keep it above 1 for not overloading the server
                            if status_code == 200:
                                utils.logger_info.info("Buoy {} Synced file {} in {}".format(current_buoy['name'], f, current_buoy['uploading_endpoint']))
                                os.remove('./{}/{}'.format(self.__mac_address, f))
                                utils.logger_info.info("Buoy {} Deleted file {}".format(current_buoy['name'], f))
                            elif retries <= 0:
                                utils.logger_info.info("Buoy {} File {} not synced, exceeded retries".format(current_buoy['name'], f))
                            else:
                                utils.logger_info.info("Buoy {} File {} not synced because API request trouble: {}".format(current_buoy['name'], f, status_code))

                except FileNotFoundError as e:
                    utils.logger_error.error("Buoy {} Allowed Exception (At the beginning, while no buoy folders have been created yet): {}".format(current_buoy['name'], e))
                except JSONDecodeError as e:
                    utils.logger_error.error("Buoy {} Allowed Exception (Probably provocated by the OS latency syncing files in folder): {}".format(current_buoy['name'], e))
                except Exception as e:
                    utils.logger_error.error("Buoy {} Exception: {}".format(current_buoy['name'], e))
                finally:
                    time.sleep(utils.SYNC_REMOTE_DIRECTORY_UPDATE_INTERVAL_SECONDS)

        process = Process(target=sync, args=(self.__mac_address,))
        process.start()
        #.join() is not needed as the while loop never ends
