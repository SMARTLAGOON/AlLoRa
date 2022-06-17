from lora_ctp.ctp_node import Node

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
	lora_node = Node(name = "C", frequency = 868000000, sf = 7,
					chunk_size = 235, mesh_mode = True, debug = False)
	try:
		clean_timing_file()
		success, backup, mesh_flag, debug_hops_flag, destination = lora_node.establish_connection()
		if success:
			print("Connected!")
			if backup:
				print(backup)
				size = int(backup.split(".")[0])
				file_counter = sizes.index(size)
				n, size, file_counter = get_next_file(sizes, file_counter)
				#lora_node.restore_file(name = '{}.json'.format(size), content = bytearray('TEST-{}'.format(n%100)))
				lora_node.restore_file(name = '{}.json'.format(size),
										content = bytearray('{}'.format(n%10)*(1024 * size)))
			while True:
				if not lora_node.got_file():
					n, size, file_counter = get_next_file(sizes, file_counter)
					lora_node.set_new_file(name = '{}.json'.format(size),
											content = bytearray('{}'.format(n%10)*(1024 * size)),
											mesh_flag = mesh_flag, debug_hops_flag = debug_hops_flag,
											destination = destination)

				mesh_flag, debug_hops_flag, destination = lora_node.send_file()

	except KeyboardInterrupt as e:
		print("THREAD_EXIT WITH ERROR: ", e)
		#THREAD_EXIT = True
