from lora_ctp.ctp_node import Node

from CampbellScientificCR1000XMockup import CampbellScientificCR1000XMockup
import utime

#Thread exit flag
#THREAD_EXIT = False

# For testing
sizes = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
file_counter = 0

def get_next_file(sizes, file_counter):
	n = file_counter % len(sizes)
	file_counter += 1
	size = sizes[n]
	return n, size, file_counter

def clean_timing_file():
	test_log = open('log.txt', "wb")
	test_log.write("")
	test_log.close()


if __name__ == "__main__":

	lora_node = Node(name = "A", frequency = 868000000, sf = 7,
					chunk_size = 235, mesh_mode = True, debug = False)

	chunk_size = lora_node.get_chunk_size()
	datasourceCR1000X = CampbellScientificCR1000XMockup(file_chunk_size=chunk_size,
													sleep_between_readings=30)
	datasourceCR1000X.start()
	try:
		clean_timing_file()
		backup = lora_node.establish_connection()	#, backup, mesh_flag, debug_hops_flag, destination
		#if success:
		print("Connected!")
		if backup:
			"""
			size = int(backup.split(".")[0])
			file_counter = sizes.index(size)
			n, size, file_counter = get_next_file(sizes, file_counter)
			#lora_node.restore_file(name = '{}.json'.format(size), content = bytearray('TEST-{}'.format(n%100)))
			lora_node.restore_file(name = '{}.json'.format(size),
									content = bytearray('{}'.format(n%10)*(1024 * size)))"""

			print("Asking backup")
			file = datasourceCR1000X.get_backup()
			lora_node.restore_file(file)

		while True:
			if not lora_node.got_file():
				print("Setting file")
				file = None
				while file == None:
					file = datasourceCR1000X.get_next_file()
				lora_node.set_file(file)
				print("New file set, ", file.get_name())
				#utime.sleep(30)
			"""if not lora_node.got_file():
				lora_node.set_new_file(file)

				n, size, file_counter = get_next_file(sizes, file_counter)

				lora_node.set_new_file(name = '{}.json'.format(size),
										content = bytearray('{}'.format(n%10)*(1024 * size)),
										mesh_flag = mesh_flag, debug_hops_flag = debug_hops_flag,
										destination = destination)"""
			#if not lora_node.got_file():
				#print("Sending file...")
			mesh_flag, debug_hops_flag, destination = lora_node.send_file()

	except KeyboardInterrupt as e:
		datasourceCR1000X.stop()
		print("THREAD_EXIT")
		THREAD_EXIT = True

'''
from CampbellScientificCR1000X import CampbellScientificCR1000X
import utime

datasourceCR1000X = CampbellScientificCR1000X(file_chunk_size=190, sleep_between_readings=30)
datasourceCR1000X.start()

counter = 1
while True:
	try:
		#file = datasourceCR1000X.get_backup()
		file = datasourceCR1000X.get_next_file()
		if file is not None:
			#print(file.get_content())
			print(counter, file.get_name())
			counter += 1
		utime.sleep(30)
	except KeyboardInterrupt as e:
		datasourceCR1000X.stop()
		break
'''
