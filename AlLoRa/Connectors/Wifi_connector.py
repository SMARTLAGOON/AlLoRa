import socket
import json
import select
from time import sleep, time

from AlLoRa.Packet import Packet
from AlLoRa.Connectors.Connector import Connector
from AlLoRa.utils.debug_utils import print

class WiFi_connector(Connector):
    def __init__(self):
        super().__init__()

    def config(self, config_json):
        super().config(config_json)
        if self.config_parameters:
            self.REQUESTER_API_HOST = self.config_parameters.get('requester_api_host', "192.168.4.1")
            self.REQUESTER_API_PORT = self.config_parameters.get('requester_api_port', 80)
            self.SOCKET_TIMEOUT = self.config_parameters.get('socket_timeout', 10)
            self.SOCKET_RECV_SIZE = self.config_parameters.get('socket_recv_size', 10000)
            self.PACKET_RETRY_SLEEP = self.config_parameters.get('packet_retry_sleep', 0.5)
            if self.debug:
                print("WiFi Connector configured: host={}, port={}, timeout={}, recv_size={}, retry_sleep={}".format(
                    self.REQUESTER_API_HOST, self.REQUESTER_API_PORT, self.SOCKET_TIMEOUT, self.SOCKET_RECV_SIZE, self.PACKET_RETRY_SLEEP
                ))

    def send_command(self, command):
        try:
            s = socket.socket()
            s.settimeout(self.SOCKET_TIMEOUT)
            addr = socket.getaddrinfo(self.REQUESTER_API_HOST, self.REQUESTER_API_PORT)[0][-1]
            s.connect(addr)

            # Prepare HTTP request
            content = json.dumps({"command": command})
            httpreq = ("POST /command HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n"
                       "Content-Type: application/json\r\nContent-Length: {}\r\n\r\n{}").format(
                           self.REQUESTER_API_HOST, len(content), content
                       )
            s.send(httpreq.encode())

            # Receive response
            response = s.recv(self.SOCKET_RECV_SIZE)
            if response:
                try:
                    extracted_response = response.decode('utf-8').split('\r\n\r\n')[1]
                    return json.loads(extracted_response)
                except Exception as e:
                    if self.debug:
                        print("Error parsing response:", e)
            return None
        except Exception as e:
            if self.debug:
                print("Error in send_command:", e)
            return None
        finally:
            try:
                s.close()
            except Exception:
                pass

    def send(self, packet: Packet):
        command = "Send:" + packet.get_content().decode()
        response = self.send_command(command)
        return response and response.get("ACK") == "OK"

    def send_and_wait_response(self, packet: Packet):
        command = "S&W:" + packet.get_content().decode()
        packet_size_sent = len(packet.get_content())
        response = self.send_command(command)

        if not response or "ACK" not in response:
            return {"type": "SEND_ERROR", "message": "No ACK received"}, packet_size_sent, 0, 0

        try:
            self.adaptive_timeout = float(response["ACK"]) + 0.5
        except Exception as e:
            return {"type": "PARSE_ERROR", "message": str(e)}, packet_size_sent, 0, 0

        t0 = time()
        received_data = self.recv(self.adaptive_timeout)
        td = time() - t0
        if received_data:
            response_packet = Packet(self.mesh_mode, self.short_mac)
            if response_packet.load(received_data):
                return response_packet, packet_size_sent, len(received_data), td
            return {"type": "CORRUPTED_PACKET", "message": "Failed to load packet"}, packet_size_sent, len(received_data), td

        return {"type": "TIMEOUT", "message": "No response received"}, packet_size_sent, 0, td

    def recv(self, focus_time):
        command = "Listen:{}".format(focus_time)
        response = self.send_command(command)

        if not response or response.get("ACK") != "OK":
            if self.debug:
                print("Listen command not acknowledged or failed")
            return None

        if "response" in response:
            return response["response"]
        elif "error" in response:
            if self.debug:
                print("Error in recv response:", response["error"])
        return None

    def change_rf_config(self, frequency=None, sf=None, bw=None, cr=None, tx_power=None, backup=True):
        command = {
            "command": "CHANGE_RF_CONFIG",
            "params": {
                "frequency": frequency,
                "sf": sf,
                "bw": bw,
                "cr": cr,
                "tx_power": tx_power,
            }
        }
        response = self.send_command(json.dumps(command))
        if response and response.get("ACK") == "OK":
            self.update_rf_params(response.get("params", {}))
            return True
        elif response and "error" in response:
            if self.debug:
                print("Error changing RF config via WiFi: {}".format(response["error"]))
        return False

    def update_rf_params(self, params):
        self.frequency = params.get("frequency", self.frequency)
        self.sf = params.get("sf", self.sf)
        self.bw = params.get("bw", self.bw)
        self.cr = params.get("cr", self.cr)
        self.tx_power = params.get("tx_power", self.tx_power)
