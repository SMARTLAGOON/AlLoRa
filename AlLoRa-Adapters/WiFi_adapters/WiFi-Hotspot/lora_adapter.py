import socket
from utime import sleep, time, ticks_ms
from uos import urandom
import gc
import ujson
import binascii
import usocket
from network import WLAN, LoRa
import pycom

from Packet import Packet

class AdapterNode:

	MAX_LENGTH_MESSAGE = 255	    # Must check if packet <= this limit to send a message

	def __init__(self, ssid, password, max_timeout = 100, frequency=868000000, sf = 7, mesh_mode = False, debug = False):
		#Enable garbage collector
		gc.enable()
		# Creation of LoRa socket
		self.sf = sf
		self.frequency = frequency
		self.__lora = LoRa(mode=LoRa.LORA, frequency=self.frequency, region=LoRa.EU868, sf = self.sf)
		self.__lora_socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
		#self.__lora_socket.setblocking(False)

		self.__WAIT_MAX_TIMEOUT = max_timeout
		self.min_timeout = 0.5
		self.adaptive_timeout = self.min_timeout
		self.backup_timeout = self.adaptive_timeout
		self.__mesh_mode = mesh_mode
		self.__DEBUG = debug

		self.__MAC = binascii.hexlify(LoRa().mac()).decode('utf-8')[8:]
		#if self.__DEBUG:
		print(self.__MAC)

		self.ssid = ssid
		wlan = WLAN()
		wlan.init(mode=WLAN.AP, ssid=ssid, auth=(WLAN.WPA2, password))
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

	def backup_config(self):
		conf = "name={}\nfreq={}\nsf={}\nmesh_mode={}\ndebug={}".format(
                self.ssid, self.frequency, self.sf,
				self.__mesh_mode, self.__DEBUG)
		with open("LoRa.conf", "w") as f:
			f.write(conf)

	def set_sf(self, sf):
		if self.sf != sf:
			self.__lora.sf(sf)
			self.sf = sf
			self.backup_config()
			if self.__DEBUG:
				print("SF Changed to: ", self.sf)

	def get_stats(self):
		stats = self.__lora.stats()
		if self.__DEBUG:
			print("rx_timestamp {0}, rssi {1}, snr {2}, sftx {3}, sfrx {4}, tx_trials {5}, tx_power {6}, tx_time_on_air {7}, tx_counter {8}, tx_frequency {9}".format(stats[0],
                    stats[1], stats[2], stats[3], stats[4], stats[5], stats[6], stats[7], stats[8], stats[9]))
		return stats

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

	def send_and_wait_response(self, packet):
		packet.set_source(self.__MAC)  # Adding mac address to packet
		send_success = self.__send(packet)
		if not send_success:
			return None

		focus_time = self.adaptive_timeout
		while focus_time > 0:
			t0 = ticks_ms()
			received_data = self.__recv(focus_time)
			td = (ticks_ms() - t0)/1000
			if not received_data:
				random_factor = int.from_bytes(urandom(2), "little") / 2**16
				self.adaptive_timeout = min(self.adaptive_timeout * (1 + random_factor),
										self.__WAIT_MAX_TIMEOUT) #random exponential backoff.
				return None
			response_packet = Packet(self.__mesh_mode)
			pycom.rgbled(0x00ecff)  # Aquamarine blue
			if self.__DEBUG:
				self.__signal_estimation()
				print("WAIT_RESPONSE({}) || sender_reply: {}".format(self.adaptive_timeout, received_data))
			try:
				response_packet.load(received_data)
				if response_packet.get_source() == packet.get_destination() and response_packet.get_destination() == self.__MAC:
					pycom.rgbled(0)
					if len(received_data) > response_packet.HEADER_SIZE + 60:	# Hardcoded for only chunks
						self.adaptive_timeout = max(self.adaptive_timeout * 0.8 + td * 0.21, self.min_timeout)
					return response_packet
			except Exception as e:
				print("Corrupted packet received", e, received_data)
				pycom.rgbled(0)
			focus_time = self.adaptive_timeout - td

	'''This function send a LoRA-CTP Packet using raw LoRa'''
	def __send(self, packet):
		if self.__DEBUG:
			print("SEND_PACKET(SF: {}) || packet: {}".format(self.sf, packet.get_content()))
		if packet.get_length() <= AdapterNode.MAX_LENGTH_MESSAGE:
			pycom.rgbled(0x007f00) # green
			self.__lora_socket.setblocking(False)
			self.__lora_socket.send(packet.get_content())
			pycom.rgbled(0)
			return True
		else:
			print("Error: Packet too big")
			return False

	def __recv(self, focus_time):
		try:
			self.__lora_socket.settimeout(focus_time)	#6 self.adaptive_timeout
			data = self.__lora_socket.recv(AdapterNode.MAX_LENGTH_MESSAGE)
			if self.__DEBUG:
				self.get_stats()
			return data
		except:
			pass

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
				response_json = ujson.loads(str(r).split("\\r\\n\\r\\n")[1][:-1]) #FIXME A comma from nowhere is sneaked into it, that is why I use slicing.
				#Response to the sender (buoy)
				packet = Packet(self.__mesh_mode)
				packet.load_dict(response_json['packet'])	#response_json['packet']
				buoy_response_packet = self.send_and_wait_response(packet)
				if buoy_response_packet:
					if buoy_response_packet.get_command():
						if buoy_response_packet.get_debug_hops():
							buoy_response_packet.add_hop("G", self.__raw_rssi(), 0)
						if buoy_response_packet.get_change_sf():
							print("OK and changing sf")
							new_sf = int(buoy_response_packet.get_payload().decode().split('"')[1])
							print(new_sf)
							self.set_sf(new_sf)
						json_buoy_response = ujson.dumps({"response_packet": buoy_response_packet.get_dict()})
						if self.__DEBUG == True:
							print("HTTP", json_buoy_response)
						clientsocket.send(http + json_buoy_response)
		except Exception as e:
			pycom.rgbled(0)
			print("Error:", e)
		# Close the socket and terminate the thread
		clientsocket.close()
