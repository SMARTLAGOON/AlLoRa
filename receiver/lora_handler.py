from network import LoRa
import socket
import time
from Packet import Packet

# Creation of LoRa socket
lora = LoRa(mode=LoRa.LORA, frequency=868000000, region=LoRa.EU868)
socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

WAIT_MAX_TIMEOUT = 100
DEBUG = False
mesh_mode = False

def print_rssi_quality_percentage():
	global lora
	global DEBUG

	percentage = 0
	rssi = lora.stats()[1]
	if (rssi >= -50):
		percentage = 100
	elif (rssi <= -50) and (rssi >= -100):
		percentage = 2 * (rssi + 100)
	elif (rssi < 100):
		percentage = 0
	if DEBUG == True:
		print('SIGNAL STRENGTH', percentage, '%')


'''
This function waits for a message to be received from a sender.
'''
def wait_sender_data(packet):
	global WAIT_MAX_TIMEOUT
	global DEBUG

	timeout = WAIT_MAX_TIMEOUT
	received = False
	received_data = b''

	socket.send(packet.get_content().encode())
	response_packet = Packet(mesh_mode = mesh_mode)
	while(timeout > 0 or received is True):

		if DEBUG == True:
			print("WAIT_SENDER_DATA() || quedan {} segundos timeout".format(timeout))
		received_data = socket.recv(256)
		print_rssi_quality_percentage()
		if DEBUG == True:
			print("WAIT_SENDER_DATA() || sender_reply: {}".format(received_data))
		if received_data.startswith(b'S:::'):
			try:
				response_packet = Packet(mesh_mode = mesh_mode)
				response_packet.load(received_data.decode('utf-8'))
				if response_packet.get_source() == packet.get_destination():
					received = True
					break
				else:
					response_packet = Packet(mesh_mode = mesh_mode)
			except Exception as e:
				print("Corrupted packet received", e)
		time.sleep(0.01)
		timeout = timeout - 1

	return response_packet


'''
This function broadcasts a message
'''
def send_packet(packet):
	global DEBUG

	socket.setblocking(False)
	if DEBUG == True:
		print("SEND_PACKET() || packet: {}".format(packet.get_content()))

	return wait_sender_data(packet)
