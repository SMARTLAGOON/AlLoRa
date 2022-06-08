#import pycom
from lora_adapter import AdapterNode

#Thread exit flag
THREAD_EXIT = False

#Debug flag
DEBUG = False

if __name__ == "__main__":
	lora_adapter = AdapterNode(ssid = "smartlagoon_land_receiver",
								password = "smartlagoonX98ASasd00de2l",
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
	serversocket.close()
