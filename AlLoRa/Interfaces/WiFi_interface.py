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
        (clientsocket, _) = self.serversocket.accept()
        clientsocket.settimeout(5)
        try:
            # Initialize an empty buffer to accumulate the request
            data = b""

            # Loop to read incoming data until headers and Content-Length are processed
            while True:
                chunk = clientsocket.recv(512)  # Read data in chunks
                if not chunk:
                    break
                data += chunk
                # Check if headers and body separator ("\r\n\r\n") are in the buffer
                if b"\r\n\r\n" in data:
                    break

            # Decode the headers and split the buffer into headers and body
            decoded_data = data.decode()
            if "\r\n\r\n" in decoded_data:
                headers, body = decoded_data.split("\r\n\r\n", 1)
            else:
                raise ValueError("Malformed HTTP request: Missing headers or body separator.")

            # Extract Content-Length from headers
            content_length = 0
            for line in headers.split("\r\n"):
                if line.startswith("Content-Length:"):
                    content_length = int(line.split(":")[1].strip())
                    break

            # Continue receiving the body if it's incomplete
            while len(body) < content_length:
                body += clientsocket.recv(512).decode()

            # Debug: Show the received HTTP request
            if self.debug:
                print(f"Received by WiFi: {decoded_data}")

            # Parse the JSON body
            request = loads(body)
            # Extract command and parameters
            command = request.get("command")
            params = request.get("data", {})

            # Debug: Show extracted command and params
            if self.debug:
                print(f"Command: {command}, Params: {params}")

            # HTTP response header
            http_response = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n"

            # Handle commands
            if command == "S&W":
                print("Handling S&W")  # Debug to confirm entry into this block
                self.handle_send_and_wait(params, clientsocket, http_response)
            elif command == "Send":
                print("Handling Send")
                self.handle_source_mode(params, clientsocket, http_response)
            elif command == "Listen":
                print("Handling Listen")
                self.handle_requester_mode(params, clientsocket, http_response)
            elif command == "CHANGE_RF_CONFIG":
                print("Handling CHANGE_RF_CONFIG")
                response = self.handle_change_rf_config(params)
                clientsocket.send(http_response + dumps(response))
            elif command == "GET_RFC":
                print("Handling GET_RFC")
                self.handle_get_rf_config(clientsocket, http_response)
            else:
                print("Invalid command received")
                self.handle_invalid_command(clientsocket, http_response)

        except Exception as e:
            if self.debug:
                print(f"Error in WiFi API: {e}")
        finally:
            clientsocket.close()

    
    def handle_send_and_wait(self, params, clientsocket, http_response):
        try:
            print("Entered handle_send_and_wait")
            print(f"Params received: {params}")

            packet = Packet(self.connector.mesh_mode, self.connector.short_mac)
            data = params.encode()
            print(f"Data to load into packet: {data}")

            check = packet.load(data)
            print(f"Packet loaded successfully: {check}")
            print(f"Packet payload: {packet.get_content()}")

            # Send initial ACK response
            ack = {"ACK": self.connector.adaptive_timeout if check else 0}
            clientsocket.send(http_response + dumps(ack))  # Initial ACK response
            if not check:
                print("Packet load failed. Exiting handle_send_and_wait.")
                return

            # Send the packet
            packet.replace_source(self.connector.get_mac())
            if self.debug:
                print("Sending packet:", packet.get_content())

            # Wait for a response
            response_packet, *_ = self.connector.send_and_wait_response(packet)
            print(f"Response packet received: {response_packet}")

            if isinstance(response_packet, dict):  # Error response
                print(f"Error in response packet: {response_packet}")
                clientsocket.send(http_response + dumps({"error": response_packet}))
            else:  # Valid packet response
                # Convert the packet to a dictionary for safe transport
                response_payload = response_packet.get_dict()
                print(f"Valid response packet: {response_payload}")
                clientsocket.send(http_response + dumps(response_payload))
        except Exception as e:
            print(f"Exception in handle_send_and_wait: {e}")
            clientsocket.send(http_response + dumps({"error": str(e)}))

    def handle_source_mode(self, params, clientsocket, http):
        packet = Packet(self.connector.mesh_mode, self.connector.short_mac)
        ack = {"ACK": "OK"}
        clientsocket.send(http + dumps(ack))
        try:
            packet.load(params.get("data", "").encode())
            packet.replace_source(self.connector.get_mac())
            self.connector.send(packet)
        except Exception as e:
            clientsocket.send(http + dumps({"error": str(e)}))

    def handle_requester_mode(self, params, clientsocket, http):
        focus_time = int(params.get("focus_time", 12))
        ack = {"ACK": "OK"}
        clientsocket.send(http + dumps(ack))
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
                return {"ACK": "OK", "params": self.connector.get_rf_config()}
            else:
                return {"error": "Failed to change RF configuration"}
        except Exception as e:
            return {"error": str(e)}

    def handle_get_rf_config(self, clientsocket, http):
        try:
            rf_config = self.connector.get_rf_config()
            response = {
                "FREQ": rf_config[0], "SF": rf_config[1], "BW": rf_config[2],
                "CR": rf_config[3], "TX_POWER": rf_config[4]
            }
            clientsocket.send(http + dumps(response))
        except Exception as e:
            clientsocket.send(http + dumps({"error": str(e)}))

    def handle_invalid_command(self, clientsocket, http):
        clientsocket.send(http + dumps({"error": "Invalid Command"}))

        