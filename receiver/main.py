from lora_adapter import AdapterNode

THREAD_EXIT = False		#Thread exit flag
DEBUG = False			#Debug flag

if __name__ == "__main__":
	lora_adapter = AdapterNode(ssid = "smartlagoon_land_receiver",
								password = "smartlagoonX98ASasd00de2l",
								sf = 7,
								max_timeout = 100, mesh_mode = True,
								debug = DEBUG)
	while True:
		try:
			if THREAD_EXIT:
				break
			lora_adapter.client_API()

		except KeyboardInterrupt as e:
			THREAD_EXIT = True
			print("THREAD_EXIT")
	lora_adapter.serversocket.close()
