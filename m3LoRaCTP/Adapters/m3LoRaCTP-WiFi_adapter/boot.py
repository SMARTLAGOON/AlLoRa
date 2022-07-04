import machine
from network import WLAN
import pycom

#Stop the blinking led
pycom.heartbeat(False)

wlan = WLAN()
wlan.init(mode=WLAN.AP, ssid="smartlagoon_land_receiver", auth=(WLAN.WPA2, "smartlagoonX98ASasd00de2l"))
print(wlan.ifconfig(id=1)) #id =1 signifies the AP interface
