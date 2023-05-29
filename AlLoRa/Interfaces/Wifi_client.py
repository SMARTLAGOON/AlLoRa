import machine
from network import WLAN
from utime import sleep
import usocket
from ujson import loads, dumps
import pycom

from AlLoRa.Interfaces.Interface import Interface
from AlLoRa.Packet import Packet

class WiFi_Client_Interface(Interface):

    def __init__(self):
        super().__init__()

    def setup(self, connector, debug, config):
        super().setup(connector, debug, config)
        if self.config_parameters:
            self.ssid = self.config_parameters['ssid']
            self.psw = self.config_parameters['psw']
            self.host = self.config_parameters['host']
            self.port = self.config_parameters['port']

            self.ip = self.config_parameters['ip']
            self.subnet_mask = self.config_parameters['subnet_mask']
            self.gateway = self.config_parameters['gateway']
            self.DNS_server = self.config_parameters['DNS_server']
        else:
            self.ssid = "AlLoRa-Adapter"
            self.psw = "AlLoRaWiFi"
            self.host = "192.168.4.1"
            self.port = 80

            self.ip = '192.168.0.16'
            self.subnet_mask = '255.255.255.0'
            self.gateway = '192.168.1.10'
            self.DNS_server = '8.8.8.8'

        #Set Wifi connection
        #ip, subnet_mask, gateway, DNS_server
        self.wlan = WLAN()
        if machine.reset_cause() != machine.SOFT_RESET:
            self.wlan.init(mode=WLAN.STA)
            # configuration below MUST match your home router settings!!# (ip, subnet_mask, gateway, DNS_server)
            self.wlan.ifconfig(config=(self.ip, self.subnet_mask, self.gateway, self.DNS_server)) # (ip, subnet_mask, gateway, DNS_server)

        self.connect()
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

    def connect(self):
        while not self.wlan.isconnected():
            try:
                # change the line below to match your network ssid, security and password
                self.wlan.connect(ssid=self.ssid, auth=(WLAN.WPA2, self.psw), timeout=5000)
                print("connecting",end='')
                while not self.wlan.isconnected():
                    sleep(1)
                    print(".",end='')
                print("connected")
                pycom.rgbled(0x007f00) # green
                sleep(3)
                pycom.rgbled(0)
                if self.debug:
                    print(self.wlan.ifconfig())
            except Exception as e:
                print("Exception connecting: ", e)

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
                print("Error:", e)
        # Close the socket and terminate the thread
        clientsocket.close()
