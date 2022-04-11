import machine
from network import WLAN
import os
import pycom

#Stop the blinking led
pycom.heartbeat(False)

#Stop Wi-Fi for avoiding possible jamming
wlan = WLAN(mode=WLAN.STA)
wlan.deinit()
