import pycom

from m3LoRaCTP.Nodes.Receiver_Node import m3LoRaCTP_Receiver
from m3LoRaCTP.Connectors.Embedded_LoRa_LoPy import LoRa_LoPy_Connector
from m3LoRaCTP.Digital_Endpoint import Digital_EndPoint


if __name__ == "__main__":

	# First, we set the connector (basyc LoRa-LoPy connection to access to the LoPy's LoRa libraries)
	connector = LoRa_LoPy_Connector(frequency = 868000000, sf = 7)
	# Then, we set up out Sender Node, with name "A", with mesh mode activated
	lora_node = m3LoRaCTP_Receiver(connector = connector, mesh_mode=True)

	# Here we setup a digital_endpoint to manage the connection to the Node
	node_nickname = "C"
	node_mac_address = "70b3d549922f4240"
	node_a = Digital_EndPoint(name=node_nickname, mac_address = node_mac_address, active = True)

	# In this loop we listen to the endpoint until we have a complete file...
	print("Starting listening to {}".format(node_mac_address))
	while True:
		file = None
		while file==None:
			file = lora_node.listen_to_endpoint(node_a, 100, return_file=True)
		file_content = file.get_content()
		print(file_content)
