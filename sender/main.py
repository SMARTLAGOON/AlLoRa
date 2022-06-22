import pycom

from lora_ctp.ctp_node import LoRA_CTP_Node
from CampbellScientificCR1000XMockup import CampbellScientificCR1000XMockup


def clean_timing_file():
	test_log = open('log.txt', "wb")
	test_log.write("")
	test_log.close()


if __name__ == "__main__":

	lora_node = LoRA_CTP_Node(name = "A", frequency = 868000000, sf = 7,
					chunk_size = 235, mesh_mode = True, debug = False)

	chunk_size = lora_node.get_chunk_size()
	datasourceCR1000X = CampbellScientificCR1000XMockup(file_chunk_size=chunk_size,
													sleep_between_readings=30)
	datasourceCR1000X.start()
	try:
		clean_timing_file()
		backup = lora_node.establish_connection()
		print("Connected!")
		if backup:
			pycom.rgbled(0xf4dc26) 								# Pikachu yellow
			print("Asking backup")
			file = datasourceCR1000X.get_backup()
			lora_node.restore_file(file)
			pycom.rgbled(0)										# LED off

		while True:
			if not lora_node.got_file():
				print("Setting file")
				pycom.rgbled(0xd74894) # Kirby Pink.
				file = None
				while file == None:
					file = datasourceCR1000X.get_next_file()
				lora_node.set_file(file)
				print("New file set, ", file.get_name())
				pycom.rgbled(0)									# LED off

			mesh_flag, debug_hops_flag, destination = lora_node.send_file()

	except KeyboardInterrupt as e:
		datasourceCR1000X.stop()
		print("THREAD_EXIT")
