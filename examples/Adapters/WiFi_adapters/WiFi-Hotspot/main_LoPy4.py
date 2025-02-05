from AlLoRa.Nodes.Adapter import Adapter
from AlLoRa.Connectors.LoPy4_connector import LoPy4_connector
from AlLoRa.Interfaces.WiFi_interface import WiFi_Interface

if __name__ == "__main__":
	lora_adapter = Adapter(LoPy4_connector(), WiFi_Interface(), "LoRaWiFi.json")
	lora_adapter.run()
