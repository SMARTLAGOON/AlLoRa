import sys
import usocket
from utime import sleep
from ujson import loads, dumps

from AlLoRa.Interfaces.Interface import Interface
from AlLoRa.Packet import Packet

try:
    # Attempt to import Pycom-specific modules
    import pycom
    from network import WLAN
    PYCOM = True
except ImportError:
    # Fallback for generic MicroPython
    import network
    PYCOM = False

class WiFi_Hotspot_Interface(Interface):

    def __init__(self):
        super().__init__()
        self.wlan = None

    def setup(self, connector, debug, config):
        super().setup(connector, debug, config)
        # Configuration parameters
        self.ssid = self.config_parameters.get('ssid', "AlLoRa-Adapter")
        self.psw = self.config_parameters.get('psw', "AlLoRaWiFi")
        self.host = self.config_parameters.get('host', "192.168.4.1")
        self.port = self.config_parameters.get('port', 80)

        # Set WiFi connection
        if PYCOM:
            self.wlan = WLAN()  # Pycom
            self.wlan.init(mode=WLAN.AP, ssid=self.ssid, auth=(WLAN.WPA2, self.psw))
        else:
            self.wlan = network.WLAN(network.AP_IF)  # Generic ESP32
            self.wlan.active(True)
            self.wlan.config(essid=self.ssid, password=self.psw)

        sleep(1)

        # Set up server socket
        self.serversocket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        self.serversocket.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
        self.serversocket.bind((self.host, self.port))
        self.serversocket.listen(1)  # Accept a maximum of 1 connection at the same time

    def client_API(self):
        # Accept the connection of the clients
        (clientsocket, address) = self.serversocket.accept()
        clientsocket.settimeout(0)
        try:
            # Receive maximum of 4096 bytes from the client (nothing special with this number)
            r = clientsocket.recv(512)	#256	#512	#1024
            # If recv() returns with 0 the other end closed the connection
            if len(r) == 0:
                clientsocket.close()
                return

            if self.debug:
                print("Received by wifi: {}".format(str(r)))

            http = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection:close \r\n\r\n" #HTTP response

            if "POST /send-packet " in str(r):
                response_json = loads(str(r).split("\\r\\n\\r\\n")[1][:-1]) #FIXME A comma from nowhere is sneaked into it, that is why I use slicing.
                #Response to the Source
                packet = Packet(self.connector.mesh_mode, self.connector.short_mac)
                packet.load_dict(response_json['packet'])
                response_packet = self.connector.send_and_wait_response(packet)
                if response_packet.get_command():
                    json_response = dumps({"response_packet": response_packet.get_dict()})
                    clientsocket.send(http + json_response)
        except Exception as e:
            if self.debug:
                print("Error Wifi hotspot:", e)
        # Close the socket and terminate the thread
        clientsocket.close()
