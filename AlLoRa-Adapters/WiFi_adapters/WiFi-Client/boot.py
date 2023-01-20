import machine
from network import WLAN
import pycom
import time
import utime

#Stop the blinking led
pycom.heartbeat(False)

with open("config.txt", "r") as f:
    wifi_config = f.readlines()
ssid = wifi_config[0].split("=")[1].strip()
psw = wifi_config[1].split("=")[1].strip()

wlan = WLAN() # get current object, without changing the mode
if machine.reset_cause() != machine.SOFT_RESET:
    wlan.init(mode=WLAN.STA)
    # configuration below MUST match your home router settings!!
    #wlan.ifconfig(config=('192.168.0.33', '255.255.255.0', '192.168.1.10', '8.8.8.8')) # (ip, subnet_mask, gateway, DNS_server)
    wlan.ifconfig(config=('192.168.0.16', '255.255.255.0', '192.168.1.10', '8.8.8.8'))
#192.168.178.107
while not wlan.isconnected():
    try:
        # change the line below to match your network ssid, security and password
        wlan.connect(ssid=ssid, auth=(WLAN.WPA2, psw), timeout=5000)
        print("connecting",end='')
        while not wlan.isconnected():
            time.sleep(1)
            print(".",end='')
        print("connected")
        pycom.rgbled(0x007f00) # green
        utime.sleep(3)
        pycom.rgbled(0)
        print(wlan.ifconfig())
    except Exception as e:
        print("Exception connecting: ", e)
