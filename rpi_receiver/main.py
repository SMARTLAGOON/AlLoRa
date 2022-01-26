import pickle
import time
from Buoy import Buoy

'''
Restores a serialized Buoy object as a way of resuming the state right where it was left.
'''
def restore_backup(buoy_mac_address: str):
    restored_buoy = Buoy(buoy_mac_address)
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
    buoy1 = restore_backup('70b3d549909cd59c')
    buoy2 = restore_backup('70b3d549933c91d4')
    buoy3 = restore_backup('70b3d54992152e85')

    while (True):
        buoy1.do_next_action()
        time.sleep(1)
        buoy2.do_next_action()
        time.sleep(1)
        buoy3.do_next_action()
        time.sleep(1)



