import socket
import select

from AlLoRa.Packet import Packet
from AlLoRa.Connectors.Connector import Connector
from AlLoRa.utils.debug_utils import print
from AlLoRa.utils.json_utils import json
from AlLoRa.utils.time_utils import get_time, current_time_ms as time, sleep, sleep_ms

class WiFi_connector(Connector):
    def __init__(self):
        super().__init__()

    def config(self, config_json):
        super().config(config_json)
        if self.config_parameters:
            self.REQUESTER_API_HOST = self.config_parameters.get('requester_api_host', "192.168.4.1")
            self.REQUESTER_API_PORT = self.config_parameters.get('requester_api_port', 80)
            self.SOCKET_TIMEOUT = self.config_parameters.get('socket_timeout', 20)  # Increased timeout
            self.SOCKET_RECV_SIZE = self.config_parameters.get('socket_recv_size', 10000)
            self.PACKET_RETRY_SLEEP = self.config_parameters.get('packet_retry_sleep', 0.5)
            if self.debug:
                print("Serial Connector configure: requester_api_host: {}, requester_api_port: {}, socket_timeout: {}, socket_recv_size: {}, packet_retry_sleep: {}".format(self.REQUESTER_API_HOST, 
                self.REQUESTER_API_PORT, self.SOCKET_TIMEOUT, self.SOCKET_RECV_SIZE, self.PACKET_RETRY_SLEEP))

    def send_command(self, command):
        try:
            s = socket.socket()
            s.settimeout(self.SOCKET_TIMEOUT)
            addr = socket.getaddrinfo(self.REQUESTER_API_HOST, self.REQUESTER_API_PORT)[0][-1]
            s.connect(addr)
            content = json.dumps(command)
            httpreq = ("POST /command HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n"
                    "Content-Type: application/json\r\nContent-Length: {}\r\n\r\n{}").format(
                        self.REQUESTER_API_HOST, len(content), content
                    )
            s.send(httpreq.encode())

            # Accumulate response in case it arrives in chunks
            response = b""
            while True:
                chunk = s.recv(self.SOCKET_RECV_SIZE)
                if not chunk:
                    break
                response += chunk

            if response:
                # Debug: Print the full raw response
                if self.debug:
                    print("Raw response received:", response.decode())

                # Split the response into multiple HTTP parts
                responses = response.decode().split("\r\n\r\n")
                parsed_responses = []
                for resp in responses[1:]:  # Skip the HTTP headers
                    try:
                        parsed_responses.append(json.loads(resp))
                    except json.JSONDecodeError:
                        continue

                # Debug: Print parsed responses
                if self.debug:
                    print("Parsed responses:", parsed_responses)

                # Return all parsed responses for further processing
                return parsed_responses[0]
            return None
        except Exception as e:
            if self.debug:
                print("Error in send_command:", e)
            return None
        finally:
            s.close()

    def send(self, packet: Packet):
        command = {"command": "Send", "data": packet.get_content().decode()}
        response = self.send_command(command)
        return response and response.get("ACK") == "OK"

    def send_and_wait_response(self, packet: Packet):
        command = {"command": "S&W", "data": packet.get_content().decode()}
        packet_size_sent = len(packet.get_content())
        responses = self.send_command(command)
      
        try:
            response_packet = Packet(self.mesh_mode, self.short_mac)
            try:
                response_packet.load_dict(responses)
                return response_packet, packet_size_sent, len(response_packet.get_content()), self.adaptive_timeout
            except Exception as e:
                return {"type": "LOAD_ERROR", "message": str(e)}, packet_size_sent, 0, self.adaptive_timeout
            
            return {"type": "TIMEOUT", "message": "No response received"}, packet_size_sent, 0, self.adaptive_timeout
        except Exception as e:
            print("Error in send_and_wait_response:", e)

    def change_rf_config(self, frequency=None, sf=None, bw=None, cr=None, tx_power=None):
        command = {
            "command": "CHANGE_RF_CONFIG",
            "params": {"frequency": frequency, "sf": sf, "bw": bw, "cr": cr, "tx_power": tx_power}
        }
        response = self.send_command(command)
        if response and response.get("ACK") == "OK":
            self.update_rf_params(response.get("params", {}))
            return True
        return False

    def get_rf_config(self):
        command = {"command": "GET_RFC"}
        response = self.send_command(command)

        if response and all(key in response for key in ["FREQ", "SF", "BW", "CR", "TX_POWER"]):
            return [
                response["FREQ"],
                response["SF"],
                response["BW"],
                response["CR"],
                response["TX_POWER"]
            ]

        # Log error for unexpected response
        if self.debug:
            print("Invalid RF config response: {}".format(response))
        return []