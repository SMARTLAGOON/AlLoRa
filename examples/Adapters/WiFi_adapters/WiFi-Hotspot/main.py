#from lora_adapter import AdapterNode
from AlLoRa.Nodes.Adapter import Adapter
from AlLoRa.Connectors.LoPy4_connector import LoPy4_connector
from AlLoRa.Interfaces.Wifi_hotspot import WiFi_Hotspot_Interface

if __name__ == "__main__":
	lora_adapter = Adapter(LoPy4_connector(), WiFi_Hotspot_Interface())
	lora_adapter.run()
