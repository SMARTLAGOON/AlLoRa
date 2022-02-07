import pickle
import time
from Buoy import Buoy

'''
Restores a serialized Buoy object as a way of resuming the state right where it was left.
'''
def restore_backup(name: str, coordinates: tuple, buoy_mac_address: str):
    #TODO Externalize in config
    restored_buoy = Buoy(name=name,
                         coordinates=coordinates,
                         mac_address=buoy_mac_address)
    try:
        with open('application_backup/buoy_{}.pickle.bak'.format(buoy_mac_address), 'rb') as fp:
            restored_buoy = pickle.load(fp)
    except Exception as e:
        print(e)
    return restored_buoy

'''
This function tries to restore a possible previous state and resumes the process.
'''
if __name__ == "__main__":
    buoy1 = restore_backup(name="Boya 1 (Isla del Barón)", coordinates=(37.6996,-0.7858,0), buoy_mac_address='70b3d549909cd59c')
    buoy2 = restore_backup(name="Boya 2 (Canal del Estacio)", coordinates=(37.7467, -0.7377, 0), buoy_mac_address='70b3d549933c91d4')
    buoy3 = restore_backup(name="Boya 3 (Rambla del Albujón)", coordinates=(37.7161, -0.8584, 0), buoy_mac_address='70b3d54992152e85')

    buoy1.sync_remote(endpoint="https://heterolistic.ucam.edu/api/applications/607816fe4e830d00204224c0/userHardSensors/61fcf9dc3ea3c800203a9d35/data")
    buoy2.sync_remote(endpoint="https://heterolistic.ucam.edu/api/applications/607816fe4e830d00204224c0/userHardSensors/61fd03813ea3c800203a9d37/data")
    buoy3.sync_remote(endpoint="https://heterolistic.ucam.edu/api/applications/607816fe4e830d00204224c0/userHardSensors/61fd03c73ea3c800203a9d39/data")

    while (True):
        buoy1.do_next_action()
        time.sleep(1)
        buoy2.do_next_action()
        time.sleep(1)
        buoy3.do_next_action()
        time.sleep(1)



