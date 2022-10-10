import machine
from network import WLAN
import pycom

#Stop the blinking led
pycom.heartbeat(False)


with open("config.txt", "r") as f:
    wifi_config = f.readlines()
ssid = wifi_config[0].split("=")[1].strip()
psw = wifi_config[1].split("=")[1].strip()
print("\n\nSSID: {}\nPASSWORD: {}\n".format(ssid, psw))

wlan = WLAN()
wlan.init(mode=WLAN.AP, ssid=ssid, auth=(WLAN.WPA2, psw))
print(wlan.ifconfig(id=1)) #id =1 signifies the AP interface
