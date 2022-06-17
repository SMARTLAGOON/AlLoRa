import json
import os
import pickle
import time
from json.decoder import JSONDecodeError
from multiprocessing.context import Process
import requests
import utils

from lora_ctp.DataSource import Digital_EndPoint, File

'''
This class helps to handle senders (buoys) in a handy way.
It mounts a basic State pattern helping with communication protocol, also saves its state just in case of a blackout or whatever.
'''
class Buoy(Digital_EndPoint):

    def __init__(self, name: str, coordinates: tuple, mac_address: str, 
                        uploading_endpoint: str, active: bool, 
                        MAX_RETRANSMISSIONS_BEFORE_MESH: int):
        
        super().__init__(name, mac_address, active, MAX_RETRANSMISSIONS_BEFORE_MESH)
        self.__coordinates = coordinates #(lat, lon, alt)
        self.uploading_endpoint = uploading_endpoint


    def set_current_file(self, file: File):
        self.current_file = file
        self.__backup()

    def set_metadata(self, metadata, hop, mesh_mode):
        super().set_metadata(metadata, hop, mesh_mode)
        #utils.logger_debug.debug("Buoy {} File {} has been set".format(self.get_name(), self.current_file.get_name()))
        self.__backup()

    def set_data(self, data, hop, mesh_mode):
        super().set_data(data, hop, mesh_mode)
        self.__backup()

    # do next action : self.__backup()

    '''
    This function saves the state of the application serializing itself.

    It also saves the data received from buoys in their specific folders.
    '''
    def __backup(self):
        utils.logger_debug.debug("Buoy {} Backing up".format(self.name))
        try:
            os.mkdir('application_backup')
        except Exception as e:
            pass
        with open('application_backup/buoy_{}.pickle.bak'.format(self.mac_address), 'wb') as fp:
            pickle.dump(self, fp)

        if self.current_file is not None and len(self.current_file.get_missing_chunks()) <= 0:
            try:
                os.mkdir(self.mac_address)
            except Exception as e:
                pass

            #TODO Remove the timestamp in filename, this is a temporal solution until datalogger arrives
            def create_filename():
                timestamp = self.current_file.get_timestamp()
                original_filename = self.current_file.get_name()
                new_filename = "{}-{}".format(timestamp, original_filename)

                directory = './{}'.format(self.mac_address)
                filenames = os.listdir(directory)

                for f in filenames:
                    existing_original_filename = f.split("-")[1]
                    if original_filename == existing_original_filename:
                        return f
                return new_filename

            with open('./{}/{}'.format(self.mac_address, create_filename()), 'wb') as fp:
                fp.write(self.current_file.get_content().encode('utf-8'))
            utils.logger_info.info("Buoy {} Saved file {} containing {}".format(self.name, self.current_file.get_name(), self.current_file.get_content().encode('utf-8')))

    #This function looks for content in a constant loop.
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
                                os.remove('./{}/{}'.format(self.mac_address, f))
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

        process = Process(target=sync, args=(self.mac_address,))
        process.start()
        #.join() is not needed as the while loop never ends
