import _thread
import machine
import pycom
import time
import os
import gc
import network
from network import LoRa
import socket
import binascii
import hashlib
from File import File
import uos


#We enable the Lora connection socket and garbage collector
gc.enable()
lora = LoRa(mode=LoRa.LORA, frequency=868000000, region=LoRa.EU868)
socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
socket.setblocking(False)

#Lora MAC
MAC = binascii.hexlify(network.LoRa().mac())

#Controls logging messages
DEBUG = True

#Thread exit flag
THREAD_EXIT = False

#datalogger mockup
READ_NEW_LOG_FILE = True
log_file = None

'''
This function prints the signal strength of the last received package over LoRa
'''
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
This function sends a response depending on which command was received
'''
def handle_command(command, type):
	global socket
	global DEBUG
	global MAC
	global log_file
	global READ_NEW_LOG_FILE

	response = None
	if type == "request-data-info":
		READ_NEW_LOG_FILE = True #It allows to load the next one
		response = "MAC:::{};;;LENGTH:::{};;;FILENAME:::{}".format(MAC.decode('utf-8'), log_file.get_length(), log_file.get_name()).encode()
	elif type == "chunk-":
		requested_chunk = int(command.decode('utf-8').split(";;;")[1].split(":::")[1].split('-')[1])
		response = "MAC:::{};;;CHUNK:::{}".format(MAC.decode('utf-8'), log_file.get_chunk(requested_chunk)).encode()

	socket.send(response)


'''
This function ensures that a received message matches the criteria of any expected message.
'''
def listen_receiver():
	global MAC
	global DEBUG

	data = socket.recv(256)
	print_rssi_quality_percentage()
	request_data_info_command = "MAC:::{};;;COMMAND:::{}".format(MAC.decode('utf-8'), 'request-data-info').encode()
	chunk_command = "MAC:::{};;;COMMAND:::{}".format(MAC.decode('utf-8'), 'chunk-').encode()
	if DEBUG == True:
		print('LISTEN_RECEIVER() || received_content', data)
		print("my mac:", MAC.decode('utf-8'))

	if data.startswith(request_data_info_command):
		handle_command(data, "request-data-info") #TODO Sacar a variable global los String de comandos
	elif data.startswith(chunk_command):
		handle_command(data, "chunk-")


'''
Function for generating realistic JSON
'''
def generate_file(file_counter):
	dissolved_oxygen = uos.urandom(1)[0] % 8 + 8
	chlorophyll = uos.urandom(1)[0] % 20
	ph = uos.urandom(1)[0] % 3 + 7
	temperature = uos.urandom(1)[0] % 30 + 1
	json = '{"dissolved_oxygen":' + str(dissolved_oxygen) + ', "chlorophyll":' + str(chlorophyll) + ', "pH":' + str(ph) + ', "temperature":' + str(temperature) +'}'
	print(json)
	file = File('{}.json'.format(file_counter), json, 200)
	return file


'''
This function mocks up an existing datalogger
'''
def read_datalogger():
	global THREAD_EXIT
	global READ_NEW_LOG_FILE
	global log_file
	global DEBUG

	file_counter = 0
	while (True):
		if THREAD_EXIT == True:
			break

		if READ_NEW_LOG_FILE == True:
			if DEBUG == True:
				print("new log_file")
			log_file = generate_file(file_counter)
			READ_NEW_LOG_FILE = False
		file_counter += 1
		time.sleep(60)


'''
This function starts the datalogger mockup and keeps a loop waiting for messages.
'''
if __name__ == "__main__":
	_thread.start_new_thread(read_datalogger, ())
	try:
		while (True):
			listen_receiver()
			gc.collect()
			time.sleep(1)
	except KeyboardInterrupt as e:
		print("THREAD_EXIT")
		THREAD_EXIT = True
