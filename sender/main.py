from lora_ctp.ctp_node import Node


#Thread exit flag
THREAD_EXIT = False

# For testing
sizes = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]	#, 1024
#sfs = [7, 8, 9, 10, 11, 12]		# For changing SF in sync with the receiver
#len_list = len(sizes)
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

	lora_node = Node(sf = 7, chunk_size = 201, mesh = True, debug = False)
	"""
	from lora_ctp.Packet import Packet
	p = Packet(mesh_mode = lora_node.__mesh)
	cs = 193
	p.set_part("CHUNK", "{}".format(0)*cs)
	p.set_destination(lora_node.__MAC)
	print(p.get_content())
	print(len(p.get_content()))
	lora_node.__lora_socket.send(p.get_content().encode())
	print("sent")"""

	try:
		clean_timing_file()
		success, backup, mesh_flag = lora_node.stablish_connection()
		if success:
			if backup:
				print(backup)
				size = int(backup.split(".")[0])
				file_counter = sizes.index(size)
				n, size, file_counter = get_next_file(sizes, file_counter)
				lora_node.restore_file(name = '{}.json'.format(size), content = bytearray('{}'.format(n%100)))
				#lora_node.restore_file(name = '{}.json'.format(size), content = bytearray('{}'.format(n%10)*(1024 * size)))
			while True:
				if not lora_node.got_file():
					n, size, file_counter = get_next_file(sizes, file_counter)
					lora_node.set_new_file(name = '{}.json'.format(size), content = bytearray('{}'.format(n%100)), mesh_flag = mesh_flag)

				mesh_flag = lora_node.send_file()
					#lora_node.send_file(name = '{}.json'.format(size), content = bytearray('{}'.format(n%10)*(1024 * size)))	#( )).encode("UTF-8") '{}'.format(n%10)*(1024 * size)	#('{}'.format(n%10)*(1024 * size)).encode("UTF-8")
					#file_counter += 1

					#test_log = open('log.txt', "rb")
					#results = '{}'.format(test_log.readlines())
					#test_log.close()
					#lora_node.send_file("results", results)
	except KeyboardInterrupt as e:
		print("THREAD_EXIT")
		THREAD_EXIT = True
