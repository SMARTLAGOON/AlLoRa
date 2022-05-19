import pickle
import time
import utils
from Buoy import Buoy

'''
Restores a serialized Buoy object as a way of resuming the state right where it was left.
'''
def restore_backup(buoy: dict):

    name = buoy['name']
    coordinates = (buoy['lat'], buoy['lon'], buoy['alt'])
    mac_address = buoy['mac_address']
    uploading_endpoint = buoy['uploading_endpoint']

    utils.logger_info.info("Restoring buoy: {}".format(buoy))
    restored_buoy = Buoy(name=name,
                         coordinates=coordinates,
                         mac_address=mac_address,
                         uploading_endpoint=uploading_endpoint,
                         mesh_mode = False)

    try:
        with open('application_backup/buoy_{}.pickle.bak'.format(mac_address), 'rb') as fp:
            restored_buoy = pickle.load(fp)
        utils.logger_info.info("Restored")
    except Exception as e:
        utils.logger_error.error("Allowed Exception (No buoy backup found, creating a new Buoy object): {} ".format(e))
    return restored_buoy

'''
This function tries to restore a possible previous state and resumes the process.
'''
if __name__ == "__main__":
    utils.logger_info.info("BuoySoftware RPI_RECEIVER")
    utils.load_config()

    for buoy in utils.load_buoys_json():
        aux_buoy = restore_backup(buoy)
        utils.BUOYS.append(aux_buoy)
        utils.BUOYS[-1].sync_remote() # This function cannot be moved into Buoy class, as when restored Process won't start over unless more logic added into Buoy class

    while (True):
        for buoy in utils.BUOYS:
            t0 = time.time()
            in_time = True
            while (in_time):
                buoy.do_next_action()
                in_time = True if time.time() - t0 < 10  else False
                time.sleep(utils.NEXT_ACTION_TIME_SLEEP)
