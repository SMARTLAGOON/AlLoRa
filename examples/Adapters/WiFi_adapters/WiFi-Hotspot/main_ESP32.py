from AlLoRa.Nodes.Adapter import Adapter
from AlLoRa.Connectors.SX127x_connector import SX127x_connector
from AlLoRa.Interfaces.WiFi_interface import WiFi_Interface

def run():
	lora_adapter = Adapter(SX127x_connector(), WiFi_Interface(), "LoRaWiFi.json")
	lora_adapter.run()

run()
