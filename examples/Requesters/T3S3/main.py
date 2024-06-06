import time, gc

from AlLoRa.Nodes.Requester import Requester
from AlLoRa.Connectors.SX127x_connector import SX127x_connector
from AlLoRa.Digital_Endpoint import Digital_Endpoint

gc.enable()

def run():
	# First, we set the connector (basic connection to access to the LoRa module)
	connector = SX127x_connector()
	# Then, we set up out Requester Node:
	lora_node = Requester(connector, config_file = "LoRa.json")

	# Here we setup a digital_endpoint to manage the connection to the Node
	node_nickname = "T"
	node_mac_address = "75e05f34" # Replace with the MAC address of the node you want to connect to
	node_a = Digital_Endpoint(name=node_nickname, mac_address = node_mac_address, active = True)

	# In this loop we listen to the endpoint until we have a complete file and print it.. (just for testing purposes)
	print("Starting listening to {}".format(node_mac_address))
	while True:
		file = None
		while file==None:
			file = lora_node.listen_to_endpoint(node_a, 100, print_file=True)
		file_content = file.get_content()
		print(file_content)
		# Erase the file from the node
		del file
		del file_content
		gc.collect()
		time.sleep(10)


run()
