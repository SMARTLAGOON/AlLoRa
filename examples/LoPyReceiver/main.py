import pycom

from AlLoRa.Nodes.Receiver import Receiver
from AlLoRa.Connectors.LoPy4_connector import LoPy4_connector
from AlLoRa.Digital_Endpoint import Digital_Endpoint


if __name__ == "__main__":

	# First, we set the connector (basyc LoRa-LoPy connection to access to the LoPy's LoRa libraries)
	connector = LoPy4_connector()
	# Then, we set up out Receiver Node:
	lora_node = Receiver(connector, config_file = "LoRa.json")

	# Here we setup a digital_endpoint to manage the connection to the Node
	node_nickname = "C"
	node_mac_address = "70b3d549922f4240"
	node_a = Digital_Endpoint(name=node_nickname, mac_address = node_mac_address, active = True)

	# In this loop we listen to the endpoint until we have a complete file...
	print("Starting listening to {}".format(node_mac_address))
	while True:
		file = None
		while file==None:
			file = lora_node.listen_to_endpoint(node_a, 100, print_file=True)
		file_content = file.get_content()
		print(file_content)
