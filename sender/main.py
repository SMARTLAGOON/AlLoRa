from lora_ctp.ctp_node import Node


#Thread exit flag
THREAD_EXIT = False

# For testing
sizes = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]	#, 1024
#sfs = [7, 8, 9, 10, 11, 12]		# For changing SF in sync with the receiver
len_list = len(sizes)
file_counter = 0


def clean_timing_file():
	test_log = open('log.txt', "wb")
	test_log.write("")
	test_log.close()


if __name__ == "__main__":

	lora_node = Node(sf = 7, chunk_size = 200, mesh = False, debug = False)
	try:
		clean_timing_file()
		success = lora_node.stablish_connection()
		if success:
			for size in sizes:
				n = file_counter % len_list
				lora_node.send_file(name = '{}.json'.format(size), content = bytearray('{}'.format(n % 10) * (1024 * size)))
				#lora_node.send_file(name = '{}.json'.format(size), content = bytearray('{}'.format(n%10)*(1024 * size)))	#( )).encode("UTF-8") '{}'.format(n%10)*(1024 * size)	#('{}'.format(n%10)*(1024 * size)).encode("UTF-8")
				file_counter += 1

				#test_log = open('log.txt', "rb")
				#results = '{}'.format(test_log.readlines())
				#test_log.close()
				#lora_node.send_file("results", results)
	except KeyboardInterrupt as e:
		print("THREAD_EXIT")
		THREAD_EXIT = True
