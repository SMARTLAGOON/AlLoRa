# Main for Adaper in Gateway Side AlLoRa
# HW: TTGO LoRa 32

from AlLoRa.Nodes.Adapter import Adapter
from AlLoRa.Connectors.SX127x_connector import SX127x_connector
from AlLoRa.Interfaces.Serial_interface import Serial_Interface

if __name__ == "__main__":

	serial_iface = Serial_Interface()
	lora_adapter = Adapter(SX127x_connector(), serial_iface)
	lora_adapter.run()



