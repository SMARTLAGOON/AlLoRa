import pickle
import utils

from Buoy import Buoy
from lora_ctp.Gateway import LoRa_CTP_Gateway
from lora_ctp.adapters.Dragino_adapter import Dragino_adapter

'''
Restores a serialized Buoy object as a way of resuming the state right where it was left.
'''
def restore_backup(buoy: dict):

    name = buoy['name']
    coordinates = (buoy['lat'], buoy['lon'], buoy['alt'])
    mac_address = buoy['mac_address']
    uploading_endpoint = buoy['uploading_endpoint']
    active = buoy["active"]
    max_retransmissions = utils.MAX_RETRANSMISSIONS_BEFORE_MESH

    utils.logger_info.info("Restoring buoy: {}".format(buoy))
    restored_buoy = Buoy(name=name,
                         coordinates=coordinates,
                         mac_address=mac_address,
                         uploading_endpoint=uploading_endpoint,
                         active=active,
                         MAX_RETRANSMISSIONS_BEFORE_MESH = max_retransmissions)
    #restored_buoy.enable_mesh()
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

    adapter = Dragino_adapter(debug=True)
    lora_gateway = LoRa_CTP_Gateway(mesh_mode = True, debug_hops = False, adapter = adapter, 
                                NEXT_ACTION_TIME_SLEEP = utils.NEXT_ACTION_TIME_SLEEP, 
                                TIME_PER_BUOY = utils.TIME_PER_BUOY)
    
    for buoy in utils.load_buoys_json():
        aux_buoy = restore_backup(buoy)
        if aux_buoy.is_active():
            utils.BUOYS.append(aux_buoy)
            if utils.SYNC_REMOTE:
                utils.BUOYS[-1].sync_remote() # This function cannot be moved into Buoy class, as when restored Process won't start over unless more logic added into Buoy class

    lora_gateway.set_datasources(utils.BUOYS)
    lora_gateway.check_datasources()
