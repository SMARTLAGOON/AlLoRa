from AlLoRa.Nodes.Adapter import Adapter
from AlLoRa.Connectors.SX127x_connector import SX127x_connector
from AlLoRa.Interfaces.Wifi_hotspot import WiFi_Hotspot_Interface

def run():
	lora_adapter = Adapter(SX127x_connector(), WiFi_Hotspot_Interface())
	lora_adapter.run()

run()
