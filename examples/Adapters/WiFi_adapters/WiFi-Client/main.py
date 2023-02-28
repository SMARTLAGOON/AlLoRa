from AlLoRa.Nodes.Adapter import Adapter
from AlLoRa.Connectors.LoPy4_connector import LoPy4_connector
from AlLoRa.Interfaces.Wifi_client import WiFi_Client_Interface

if __name__ == "__main__":
	lora_adapter = Adapter(LoPy4_connector(), WiFi_Client_Interface())
	lora_adapter.run()
