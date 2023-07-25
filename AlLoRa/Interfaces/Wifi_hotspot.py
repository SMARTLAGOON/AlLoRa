from network import WLAN
from utime import sleep
import usocket
from ujson import loads, dumps

from AlLoRa.Interfaces.Interface import Interface
from AlLoRa.Packet import Packet

class WiFi_Hotspot_Interface(Interface):

    def __init__(self):
        super().__init__()

    def setup(self, connector, debug, config):
        super().setup(connector, debug, config)
        if self.config_parameters:
            self.ssid = self.config_parameters['ssid']
            self.psw = self.config_parameters['psw']
            self.host = self.config_parameters['host']
            self.port = self.config_parameters['port']
        else:
            self.ssid = "AlLoRa-Adapter"
            self.psw = "AlLoRaWiFi"
            self.host = "192.168.4.1"
            self.port = 80

        #Set Wifi connection
        wlan = WLAN()
        wlan.init(mode=WLAN.AP, ssid=self.ssid, auth=(WLAN.WPA2, self.psw))
        #print(wlan.ifconfig(id=1)) #id =1 signifies the AP interface
        sleep(1)
        # Set up server socket
        self.serversocket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        self.serversocket.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
        self.serversocket.bind((self.host, self.port))
        # Accept maximum of 1 connection at the same time.
        self.serversocket.listen(1)		#We only need one connection thread since
                                        #it is just an rpi_receiver connected,
                                        #plus, otherwise also threading memory
                                        #problems may arise, so, as a preventive
                                        #fix, threading was removed.

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
                #Response to the sender
                packet = Packet(self.connector.mesh_mode)
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
