from lora_adapter import AdapterNode

THREAD_EXIT = False		#Thread exit flag

def open_backup():
	with open("LoRa.txt", "r") as f:
		lora_config = f.readlines()

	name = lora_config[0].split("=")[1].strip()
	freq = int(lora_config[1].split("=")[1].strip())
	sf = int(lora_config[2].split("=")[1].strip())
	mesh_mode = lora_config[3].split("=")[1].strip() == "True"
	debug = lora_config[4].split("=")[1].strip() == "True"
	if debug:
		print(name, freq, sf, mesh_mode, debug)
	return name, freq, sf, mesh_mode, debug

if __name__ == "__main__":
	name, freq, sf, mesh_mode, debug = open_backup()
	lora_adapter = AdapterNode(ssid = "smartlagoon_land_receiver",
								password = "smartlagoonX98ASasd00de2l",
								sf = sf,
								max_timeout = 12, mesh_mode = mesh_mode,
								debug = debug)
	while True:
		try:
			if THREAD_EXIT:
				break
			lora_adapter.client_API()

		except KeyboardInterrupt as e:
			THREAD_EXIT = True
			print("THREAD_EXIT")
	lora_adapter.serversocket.close()
