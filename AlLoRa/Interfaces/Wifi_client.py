import machine
import sys
import usocket
from utime import sleep
from ujson import loads, dumps

from AlLoRa.Interfaces.Interface import Interface
from AlLoRa.Packet import Packet

# Attempt to import Pycom-specific modules and set a flag
PYCOM = False
try:
    import pycom
    from network import WLAN
    PYCOM = True
except ImportError:
    # Fallback for generic MicroPython
    import network
    PYCOM = False

class WiFi_Client_Interface(Interface):

    def __init__(self):
        super().__init__()

    def setup(self, connector, debug, config):
        super().setup(connector, debug, config)
        self.configure_parameters(config)

        # Set WiFi connection
        self.init_wlan()
        self.connect()

        sleep(1)
        # Set up server socket
        self.setup_socket()

    def configure_parameters(self, config):
        self.ssid = config.get('ssid', "AlLoRa-Adapter")
        self.psw = config.get('psw', "AlLoRaWiFi")
        self.host = config.get('host', "192.168.4.1")
        self.port = config.get('port', 80)
        self.ip = config.get('ip', '192.168.0.16')
        self.subnet_mask = config.get('subnet_mask', '255.255.255.0')
        self.gateway = config.get('gateway', '192.168.1.10')
        self.DNS_server = config.get('DNS_server', '8.8.8.8')

    def init_wlan(self):
        if PYCOM:
            self.wlan = WLAN()
            if machine.reset_cause() != machine.SOFT_RESET:
                self.wlan.init(mode=WLAN.STA)
                self.wlan.ifconfig(config=(self.ip, self.subnet_mask, self.gateway, self.DNS_server))
        else:
            self.wlan = network.WLAN(network.STA_IF)
            self.wlan.active(True)
            if not self.wlan.isconnected():
                self.wlan.connect(self.ssid, self.psw)
                while not self.wlan.isconnected():
                    pass  # Wait for connection

    def setup_socket(self):
        self.serversocket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        self.serversocket.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
        self.serversocket.bind((self.host, self.port))
        self.serversocket.listen(1)  # Accept a maximum of 1 connection at the same time

    def connect(self):
        while not self.wlan.isconnected():
            try:
                self.wlan.connect(self.ssid, auth=(network.WLAN.WPA2, self.psw), timeout=5000)
                if self.debug:
                    print("connecting", end='')
                while not self.wlan.isconnected():
                    sleep(1)
                    if self.debug:
                        print(".", end='')
                if self.debug:
                    print("connected")
                if PYCOM:
                    pycom.rgbled(0x007f00)  # Green
                    sleep(3)
                    pycom.rgbled(0)
                if self.debug:
                    print(self.wlan.ifconfig())
            except Exception as e:
                if self.debug:
                    print("Exception connecting:", e)

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
                print("Error:", e)
        # Close the socket and terminate the thread
        clientsocket.close()
