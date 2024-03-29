# Main for Gateway Side AlLoRa
# HW: Raspberry Pi + TTGO Adapter

import  sys, gc
from AlLoRa.Nodes.Gateway import Gateway
from AlLoRa.Connectors.Serial_connector import Serial_connector


if __name__ == "__main__":
	connector = Serial_connector()
	allora_gateway = Gateway(connector, config_file= "LoRa.json", debug_hops= False, TIME_PER_ENDPOINT=10)

	# Listen to the digital_endpoints and print and save the files as they come in
	allora_gateway.check_digital_endpoints(print_file_content = True, save_files = True)
	
	
