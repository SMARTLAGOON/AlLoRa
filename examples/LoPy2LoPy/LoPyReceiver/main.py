import pycom

from mLoRaCTP.Nodes.Sender_Node import mLoRaCTP_Receiver
from mLoRaCTP.Connectors.Embedded_LoRa_LoPy import LoRa_LoPy_Connector
from mLoRaCTP.mLoRaCTP_File import CTP_File
from time import sleep



if __name__ == "__main__":

	# First, we set the connector (basyc LoRa-LoPy connection to access to the LoPy's LoRa libraries)
	connector = LoRa_LoPy_Connector(frequency = 868000000, sf = 7)

	# Then, we set up out Sender Node, with name "A", with mesh mode activated
	lora_node = mLoRaCTP_Receiver(name = "A", connector = connector, mesh_mode = True)
	
	# Work in progress