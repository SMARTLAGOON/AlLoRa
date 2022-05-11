from network import LoRa
import socket
import time

# Creation of LoRa socket
lora = LoRa(mode=LoRa.LORA, frequency=868000000, region=LoRa.EU868, sf=7)
socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

WAIT_MAX_TIMEOUT = 10
DEBUG = True

def print_rssi_quality_percentage():
	global lora

	percentage = 0
	rssi = lora.stats()[1]
	if (rssi >= -50):
		percentage = 100
	elif (rssi <= -50) and (rssi >= -100):
		percentage = 2 * (rssi + 100)
	elif (rssi < 100):
		percentage = 0
	print('SIGNAL STRENGTH', percentage, '%')


'''
This function waits for a message to be received from a sender.
'''
def wait_sender_data(buoy_mac_address):
	global WAIT_MAX_TIMEOUT
	global DEBUG

	timeout = WAIT_MAX_TIMEOUT
	received_data = b''

	while(timeout > 0):
		if DEBUG == True:
			print_rssi_quality_percentage()
			print("WAIT_SENDER_DATA() || quedan {} segundos timeout".format(timeout))
		received_data = socket.recv(256)
		if DEBUG:
			print_rssi_quality_percentage()
			print("WAIT_SENDER_DATA() || sender_reply: {}".format(received_data))
		if received_data.startswith(b'S:::'):
			try:
				response_packet = Packet()
				response_packet.load(received_data.decode('utf-8'))
				if response_packet.get_source() == packet.get_destination():
					received = True
					break
				else:
					response_packet = Packet()
			except Exception as e:
				print("Corrupted packet received", e)
		time.sleep(0.1) #MERGE
		timeout = timeout - 1

	return received_data


'''
This function broadcasts a message
'''
def send_command(command, buoy_mac_address):
	global DEBUG

	socket.setblocking(False)
	if DEBUG:
		print("SEND_COMMAND() || command: {}".format(command))
	socket.send(command.encode())
	return wait_sender_data(buoy_mac_address)
