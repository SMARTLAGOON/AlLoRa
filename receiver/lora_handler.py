from network import LoRa
import socket
import time

# Creation of LoRa socket
lora = LoRa(mode=LoRa.LORA, frequency=868000000, region=LoRa.EU868)
socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

WAIT_MAX_TIMEOUT = 10
DEBUG = False

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
def wait_sender_data(buoy_mac_address):
	global WAIT_MAX_TIMEOUT
	global DEBUG

	timeout = WAIT_MAX_TIMEOUT
	received_data = b''

	while(timeout > 0):
		if DEBUG == True:
			print("WAIT_SENDER_DATA() || quedan {} segundos timeout ({})".format(timeout, buoy_mac_address))
		received_data = socket.recv(256)
		print_rssi_quality_percentage()
		if DEBUG == True:
			print("WAIT_SENDER_DATA() || sender_reply: {}".format(received_data))
		if received_data.startswith(b'MAC:::'):
			source_mac_address = received_data.decode('utf-8').split(";;;")[0].split(":::")[1]
			if source_mac_address == buoy_mac_address:
				received = True
				break
		#time.sleep(1)	# Reducir
		timeout = timeout - 1

	return received_data


'''
This function broadcasts a message
'''
def send_command(command, buoy_mac_address):
	global DEBUG

	socket.setblocking(False)
	if DEBUG == True:
		print("SEND_COMMAND() || command: {}".format(command))
	socket.send(command.encode())
	return wait_sender_data(buoy_mac_address)
