import socket
import time
import gc
import ujson
import binascii
import usocket
import time
from network import LoRa, WLAN

from m3LoRaCTP_Packet import Packet

class AdapterNode:

	MAX_LENGTH_MESSAGE = 255    # Must check if packet <= this limit to send a message

	def __init__(self, ssid, password, max_timeout = 100, sf = 7, mesh_mode = False, debug = False):
		#Enable garbage collector
		gc.enable()
		# Creation of LoRa socket
		self.__lora = LoRa(mode=LoRa.LORA, frequency=868000000, region=LoRa.EU868, sf = sf)
		self.__lora_socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
		#self.__lora_socket.setblocking(False)

		self.__WAIT_MAX_TIMEOUT = max_timeout
		self.__mesh_mode = mesh_mode
		self.__DEBUG = debug

		self.__MAC = binascii.hexlify(LoRa().mac()).decode('utf-8')[8:]
		#if self.__DEBUG:
		print(self.__MAC)

		"""
		wlan = WLAN()
		wlan.init(mode=WLAN.AP, ssid=ssid, auth=(WLAN.WPA2, password))"""
		#print(wlan.ifconfig(id=1)) #id =1 signifies the AP interface
		time.sleep(1)
		# Set up server socket
		self.serversocket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
		self.serversocket.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
		self.serversocket.bind(("0.0.0.0", 5550))
		# Accept maximum of 1 connection at the same time.
		self.serversocket.listen(1)		#We only need one connection thread since
										#it is just an rpi_receiver connected,
										#plus, otherwise also threading memory
										#problems may arise, so, as a preventive
										#fix, threading was removed.

	# LoRa methods
	""" This function returns the RSSI of the last received packet"""
	def __raw_rssi(self):
		return self.__lora.stats()[1]

	def __signal_estimation(self):
		percentage = 0
		rssi = self.__raw_rssi()
		if (rssi >= -50):
			percentage = 100
		elif (rssi <= -50) and (rssi >= -100):
			percentage = 2 * (rssi + 100)
		elif (rssi < 100):
			percentage = 0
		print('SIGNAL STRENGTH', percentage, '%')

	"""This function waits for a message to be received from a sender using raw LoRa"""
	def send_and_wait_response(self, packet):
		packet.set_source(self.__MAC)		# Adding mac address to packet
		success = self.__send(packet)
		response_packet = Packet(self.__mesh_mode)	# = mesh_mode
		if success:
			timeout = self.__WAIT_MAX_TIMEOUT
			received = False
			received_data = b''
			while(timeout > 0 or received is True):
				if self.__DEBUG:
					print("WAIT_RESPONSE() || quedan {} segundos timeout".format(timeout))
				received_data = self.__recv()
				if received_data:
					if self.__DEBUG:
						self.__signal_estimation()
						print("WAIT_WAIT_RESPONSE() || sender_reply: {}".format(received_data))
					#if received_data.startswith(b'S:::'):
					try:
						response_packet = Packet(self.__mesh_mode)	# = mesh_mode
						response_packet.load(received_data)	#.decode('utf-8')
						if response_packet.get_source() == packet.get_destination():
							received = True
							break
						else:
							response_packet = Packet(self.__mesh_mode)	# = mesh_mode
					except Exception as e:
						print("Corrupted packet received", e, received_data)
				time.sleep(0.01)
				timeout -= 1
		return response_packet

	'''This function send a LoRA-CTP Packet using raw LoRa'''
	def __send(self, packet):
		if self.__DEBUG:
			print("SEND_PACKET() || packet: {}".format(packet.get_content()))
		if packet.get_length() <= AdapterNode.MAX_LENGTH_MESSAGE:
			self.__lora_socket.send(packet.get_content())	#.encode()
			return True
		else:
			print("Error: Packet too big")
			return False

	def __recv(self, size=256):
		self.__lora_socket.settimeout(6)
		data = self.__lora_socket.recv(size)
		self.__lora_socket.setblocking(False)
		return data

	#def __recv(self):
		#return self.__lora_socket.recv(256)

	'''
	This function runs an HTTP API that serves as a LoRa forwarder for the rpi_receiver that connects to it
	'''
	def client_API(self):
		# Accept the connection of the clients
		if self.__DEBUG:
			print("Socket accept...")
		(clientsocket, address) = self.serversocket.accept()
		gc.collect()
		clientsocket.settimeout(0)
		if self.__DEBUG:
			print("Socket ok...")
		try:
			# Receive maximum of 4096 bytes from the client (nothing special with this number)
			if self.__DEBUG:
				print("Waiting for next message")
			r = clientsocket.recv(1024)	#256	#512
			# If recv() returns with 0 the other end closed the connection
			if len(r) == 0:
				clientsocket.close()
				return
			else:
				if self.__DEBUG:
					print("Received: {}".format(str(r)))

			http = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection:close \r\n\r\n" #HTTP response

			if "POST /send-packet "in str(r):
				response_json = ujson.loads(str(r).split("\\r\\n\\r\\n")[1][:-1]) #FIXME A comma from nowhere is sneaked into it, that is why I use slicing.
				#Response to the sender (buoy)
				packet = Packet(self.__mesh_mode)
				packet.load_dict(response_json['packet'])	#response_json['packet']
				buoy_response_packet = self.send_and_wait_response(packet)
				if buoy_response_packet.get_command():
					if buoy_response_packet.get_debug_hops():
						buoy_response_packet.add_hop("G", self.__raw_rssi(), 0)
					#print(buoy_response_packet.get_content())
					json_buoy_response = ujson.dumps({"response_packet": buoy_response_packet.get_dict()})	#get_content()
					if self.__DEBUG == True:
						print("HTTP", json_buoy_response)
					clientsocket.send(http + json_buoy_response)
		except Exception as e:
			print("Error:", e)
		# Close the socket and terminate the thread
		clientsocket.close()
