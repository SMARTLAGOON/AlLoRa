import socket
from utime import sleep, ticks_ms
from uos import urandom
import gc
import binascii
import usocket
from network import WLAN#, LoRa
import pycom
from ujson import loads, dumps

from AlLoRa.Packet import Packet

class AdapterNode:

	MAX_LENGTH_MESSAGE = 255	    # Must check if packet <= this limit to send a message

	def __init__(self, connector, config_file = "LoRa.json"):
		#Enable garbage collector
		gc.enable()

		self.config_file = config_file
		self.open_backup()

		self.connector = connector
		self.connector.config(name = self.__name, frequency = self.frequency,
								sf = self.sf,
								mesh_mode = self.mesh_mode,
								debug = self.__DEBUG,
								min_timeout = self.min_timeout,
								max_timeout = self.max_timeout)


		self.__MAC = self.connector.get_mac()[8:]
		print(self.__MAC)

		self.adaptive_timeout = self.min_timeout
		self.backup_timeout = self.adaptive_timeout

		self.setup_API()

	def open_backup(self):
		with open(self.config_file, "r") as f:
			lora_config = loads(f.read())

		self.__name = lora_config['name']
		self.frequency = lora_config['freq']
		self.sf = lora_config['sf']
		self.mesh_mode = lora_config['mesh_mode']
		self.__DEBUG = lora_config['debug']
		self.min_timeout = lora_config['min_timeout']
		self.max_timeout  = lora_config['max_timeout']

		self.ssid = lora_config['ssid']
		self.psw = lora_config['psw']
		if self.__DEBUG:
			print(lora_config)

	def setup_API(self):
		#Set Wifi connection
		wlan = WLAN()
		wlan.init(mode=WLAN.AP, ssid=self.ssid, auth=(WLAN.WPA2, self.psw))
		#print(wlan.ifconfig(id=1)) #id =1 signifies the AP interface
		sleep(1)
		# Set up server socket
		self.serversocket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
		self.serversocket.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
		self.serversocket.bind(("192.168.4.1", 80))
		#self.serversocket.bind(("192.168.0.16", 5550))
		# Accept maximum of 1 connection at the same time.
		self.serversocket.listen(1)		#We only need one connection thread since
										#it is just an rpi_receiver connected,
										#plus, otherwise also threading memory
										#problems may arise, so, as a preventive
										#fix, threading was removed.

	def run(self):
		THREAD_EXIT = False		#Thread exit flag
		while True:
			try:
				if THREAD_EXIT:
					break
				self.client_API()

			except KeyboardInterrupt as e:
				THREAD_EXIT = True
				print("THREAD_EXIT")
		self.serversocket.close()

	def backup_config(self):
		conf = {"name": self.__name,
				"chunk_size": self.__chunk_size,
				"mesh_mode": self.mesh_mode,
				"debug": self.__DEBUG,
				"sf": self.connector.sf,
				"freq": self.connector.frequency,
				"min_timeout": self.min_timeout,
				"max_timeout": self.max_timeout,
				"ssid": self.ssid,
				"psw": self.psw
				}
		with open(self.config_file, "w") as f:
			f.write(dumps(conf))

	'''
	This function runs an HTTP API that serves as a LoRa forwarder for the rpi_receiver that connects to it
	'''
	def client_API(self):
		# Accept the connection of the clients
		(clientsocket, address) = self.serversocket.accept()
		gc.collect()
		clientsocket.settimeout(0)
		try:
			# Receive maximum of 4096 bytes from the client (nothing special with this number)
			r = clientsocket.recv(512)	#256	#512	#1024
			# If recv() returns with 0 the other end closed the connection
			if len(r) == 0:
				clientsocket.close()
				return
			else:
				if self.__DEBUG:
					print("Received by wifi: {}".format(str(r)))

			http = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection:close \r\n\r\n" #HTTP response

			if "POST /send-packet "in str(r):
				response_json = loads(str(r).split("\\r\\n\\r\\n")[1][:-1]) #FIXME A comma from nowhere is sneaked into it, that is why I use slicing.
				#Response to the sender
				packet = Packet(self.mesh_mode)
				packet.load_dict(response_json['packet'])
				response_packet = self.connector.send_and_wait_response(packet)
				if response_packet:
					if response_packet.get_command():
						json_response = dumps({"response_packet": response_packet.get_dict()})
						if self.__DEBUG == True:
							print("HTTP", json_response)
						clientsocket.send(http + json_response)
		except Exception as e:
			pycom.rgbled(0)
			print("Error:", e)
		# Close the socket and terminate the thread
		clientsocket.close()
