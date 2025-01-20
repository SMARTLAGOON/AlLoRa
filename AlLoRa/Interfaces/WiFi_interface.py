import usocket
from utime import sleep
from ujson import loads, dumps
import sys

from AlLoRa.Interfaces.Interface import Interface
from AlLoRa.Packet import Packet
from AlLoRa.utils.debug_utils import print

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


class WiFi_Interface(Interface):
    def __init__(self):
        super().__init__()
        self.wlan = None

    def setup(self, connector, debug, config):
        super().setup(connector, debug, config)

        # Configuration parameters
        self.mode = config.get('mode', 'client')  # 'client' or 'hotspot'
        self.ssid = config.get('ssid', "AlLoRa-Adapter")
        self.psw = config.get('psw', "AlLoRaWiFi")
        self.host = config.get('host', "192.168.4.1")
        self.port = config.get('port', 80)
        self.ip = config.get('ip', '192.168.0.16')  # Used only for Pycom client
        self.subnet_mask = config.get('subnet_mask', '255.255.255.0')  # Pycom client
        self.gateway = config.get('gateway', '192.168.1.10')  # Pycom client
        self.DNS_server = config.get('DNS_server', '8.8.8.8')  # Pycom client

        # Initialize WiFi based on mode
        self.init_wifi()

        sleep(1)

        # Set up server socket
        self.serversocket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        self.serversocket.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
        self.serversocket.bind((self.host, self.port))
        self.serversocket.listen(1)  # Accept a maximum of 1 connection at the same time

    def init_wifi(self):
        if self.mode == 'hotspot':
            if PYCOM:
                self.wlan = WLAN()
                self.wlan.init(mode=WLAN.AP, ssid=self.ssid, auth=(WLAN.WPA2, self.psw))
            else:
                self.wlan = network.WLAN(network.AP_IF)
                self.wlan.active(True)
                self.wlan.config(essid=self.ssid, password=self.psw)
        elif self.mode == 'client':
            if PYCOM:
                self.wlan = WLAN()
                if machine.reset_cause() != machine.SOFT_RESET:
                    self.wlan.init(mode=WLAN.STA)
                    self.wlan.ifconfig(config=(self.ip, self.subnet_mask, self.gateway, self.DNS_server))
                self.connect()
            else:
                self.wlan = network.WLAN(network.STA_IF)
                self.wlan.active(True)
                self.connect()

    def connect(self):
        while not self.wlan.isconnected():
            try:
                self.wlan.connect(self.ssid, self.psw)
                if self.debug:
                    print("Connecting to WiFi...", end='')
                while not self.wlan.isconnected():
                    sleep(1)
                    if self.debug:
                        print(".", end='')
                if PYCOM:
                    pycom.rgbled(0x007f00)  # Green LED for Pycom
                    sleep(3)
                    pycom.rgbled(0)
            except Exception as e:
                if self.debug:
                    print("Exception connecting to WiFi:", e)

    def client_API(self):
        (clientsocket, address) = self.serversocket.accept()
        clientsocket.settimeout(0)
        try:
            r = clientsocket.recv(512)
            if len(r) == 0:
                clientsocket.close()
                return

            if self.debug:
                print("Received by WiFi: {}".format(str(r)))

            http = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection:close \r\n\r\n"
            request = loads(str(r).split("\\r\\n\\r\\n")[1][:-1])

            if request["command"] == "CHANGE_RF_CONFIG":
                response = self.handle_change_rf_config(request["params"])
                clientsocket.send(http + dumps(response))
            else:
                clientsocket.send(http + dumps({"error": "Invalid Command"}))
        except Exception as e:
            if self.debug:
                print("Error in WiFi API:", e)
        finally:
            clientsocket.close()

    def handle_send_and_wait(self, command, clientsocket, http):
        packet = Packet(self.connector.mesh_mode, self.connector.short_mac)
        data = command.split("S&W:")[-1]
        check = packet.load(data)

        ack = {"ACK": self.connector.adaptive_timeout if check else 0}
        clientsocket.send(http + dumps(ack))

        if not check:
            return False

        packet.replace_source(self.connector.get_mac())
        response_packet, packet_size_sent, packet_size_received, time_pr = self.connector.send_and_wait_response(packet)

        if isinstance(response_packet, dict):  # Handle errors
            clientsocket.send(http + dumps({"error": response_packet}))
            return False

        if response_packet:
            clientsocket.send(http + dumps({"response_packet": response_packet.get_dict()}))
            return True
        else:
            clientsocket.send(http + dumps({"error": "No Response"}))
            return False

    def handle_source_mode(self, command, clientsocket, http):
        packet = Packet(self.connector.mesh_mode, self.connector.short_mac)
        ack = {"ACK": "OK"}
        clientsocket.send(http + dumps(ack))

        try:
            packet.load(command.split("Send:")[-1])
            packet.replace_source(self.connector.get_mac())
            success = self.connector.send(packet)
            return success
        except Exception as e:
            clientsocket.send(http + dumps({"error": str(e)}))
            return False

    def handle_requester_mode(self, command, clientsocket, http):
        focus_time = int(command.split("Listen:")[-1])
        ack = {"ACK": "OK"}
        clientsocket.send(http + dumps(ack))

        if self.debug:
            print("Listening for: ", focus_time)

        data = self.connector.recv(focus_time)
        if data:
            try:
                packet = Packet(self.connector.mesh_mode, self.connector.short_mac)
                packet.load(data)
                clientsocket.send(http + dumps({"response": packet.get_dict()}))
            except Exception as e:
                clientsocket.send(http + dumps({"error": str(e)}))
        else:
            clientsocket.send(http + dumps({"error": "No Data Received"}))

    def handle_change_rf_config(self, params):
        try:
            success = self.connector.change_rf_config(
                frequency=params.get("frequency"),
                sf=params.get("sf"),
                bw=params.get("bw"),
                cr=params.get("cr"),
                tx_power=params.get("tx_power"),
            )
            if success:
                return {
                    "ACK": "OK",
                    "params": self.connector.get_rf_config()
                }
            else:
                return {"error": "Failed to change RF configuration"}
        except Exception as e:
            return {"error": str(e)}
        