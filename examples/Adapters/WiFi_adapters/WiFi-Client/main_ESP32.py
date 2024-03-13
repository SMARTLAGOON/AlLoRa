from AlLoRa.Nodes.Adapter import Adapter
from AlLoRa.Connectors.SX127x_connector import SX127x_connector
from AlLoRa.Interfaces.Wifi_client import WiFi_Client_Interface

if __name__ == "__main__":
	lora_adapter = Adapter(SX127x_connector(), WiFi_Client_Interface())
	lora_adapter.run()
