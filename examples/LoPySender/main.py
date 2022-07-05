import pycom

from m3LoRaCTP.Nodes.Sender_Node import m3LoRaCTP_Sender
from m3LoRaCTP.Connectors.Embedded_LoRa_LoPy import LoRa_LoPy_Connector
from m3LoRaCTP.m3LoRaCTP_File import CTP_File
from time import sleep

# For testing
sizes = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]	#, 1024
file_counter = 0

def clean_timing_file():
	test_log = open('log.txt', "wb")
	test_log.write("")
	test_log.close()


if __name__ == "__main__":

	# First, we set the connector (basyc LoRa-LoPy connection to access to the LoPy's LoRa libraries)
	connector = LoRa_LoPy_Connector(frequency = 868000000, sf = 7)

	# Then, we set up out Sender Node, with name "A", with mesh mode activated
	lora_node = m3LoRaCTP_Sender(name = "C", connector = connector, mesh_mode = True)

	# We turn on a led for a second to know that we are doing ok...
	pycom.rgbled(0x1aa7ec) 	# Picton Blue
	sleep(1)
	pycom.rgbled(0) 		# off

	chunk_size = lora_node.get_chunk_size()		# We use it to create the files to be sent...

	try:
		clean_timing_file()
		backup = lora_node.establish_connection()
		print("Connected!")

		# This is how to handle a backup file if needed (not implemented in this example...)
		if backup:
			print("Asking backup")
			#file = Datasource.get_backup()
			#lora_node.restore_file(file)

		# with an established connection, we start sending data periodically
		while True:
			if not lora_node.got_file():
				n = file_counter % len(sizes)
				file_counter += 1
				size = sizes[n]
				print("Setting file")
				pycom.rgbled(0xd74894)							# Kirby Pink.

				file = CTP_File(name = '{}.json'.format(size),
								content = bytearray('{}'.format(n%10)*(1024 * size)),
								chunk_size=chunk_size)
				lora_node.set_file(file)

				print("New file set, ", file.get_name())
				pycom.rgbled(0)									# LED off

			lora_node.send_file()

	except KeyboardInterrupt as e:
		print("THREAD_EXIT")