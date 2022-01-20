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
import _thread
'''
#We enable the Lora connection socket and garbage collector
gc.enable()
lora = LoRa(mode=LoRa.LORA, frequency=868000000, region=LoRa.EU868)
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setblocking(False)

#Lora MAC
mac = binascii.hexlify(network.LoRa().mac())
filename_counter = 0

#These are polling timeouts
WAIT_MAX_TIMEOUT = 10
WAIT_MAX_TRIALS = 60

DEBUG = False


def listen_receiver():
	global mac
	global DEBUG

	go_ahead = False

	data = s.recv(256)
	expected_content = "MAC:::{};;;COMMAND:::{}".format(mac.decode('utf-8'), 'REQUESTING_DATA').encode()
	if DEBUG == True:
		print('LISTEN_RECEIVER() || expected_content', expected_content)
		print('LISTEN_RECEIVER() || receivced_content', data)
	if data == expected_content:
		go_ahead = True
	return go_ahead


This function waits for a reply by the receiver after the data has been sent.

def wait(message_dict):
	global WAIT_MAX_TIMEOUT
	global DEBUG

	timeout = WAIT_MAX_TIMEOUT
	received = False

	while(timeout > 0):
		if DEBUG == True:
			print("WAIT() || quedan {} segundos timeout".format(timeout))
		data = s.recv(256)
		v_code = message_dict['V_CODE'] #This is a message identifier
		expected_content = "V_CODE:::{}".format(v_code).encode()
		if DEBUG == True:
			print("WAIT() || expected_reply: {}".format(expected_content))
			print("WAIT() || receiver_reply: {}".format(data))

		if data == expected_content:
			received = True
			break
		time.sleep(1)
		timeout = timeout - 1

	return received


Sends over LoRa the message, hoping on the other end the receiver is listening and gives a reply immediately after.
This function manages the max trials.

def send_data_to_receiver(message_dict):
	global s
	global WAIT_MAX_TRIALS
	global DEBUG

	max_trials = WAIT_MAX_TRIALS
	data = "MAC:::{};;;V_CODE:::{};;;FILENAME:::{};;;CONTENT:::{}".format(message_dict['MAC'], message_dict['V_CODE'], message_dict['FILENAME'], message_dict['CONTENT']).encode()

	while (max_trials > 0):
		if DEBUG == True:
			print("SEND_DATA_TO_RECEIVER() || quedan {} intentos".format(max_trials))
		s.send(data)
		if DEBUG == True:
			print("SEND_DATA_TO_RECEIVER() || sent data: {}".format(data))
		received = wait(message_dict) #Puede salir porque se ha recibido el mensaje o porque se ha agotado el tiempo
		if received is True:
			break
		max_trials = max_trials -1


This is a provisional function while datalogger is not under our domain.
It only generates a mocked message.

def get_new_message_dict():
	global filename_counter
	global mac
	global s
	global lora

	v_code = mac + str(machine.rng() & 0x0F)

	message_dict = dict()
	message_dict['MAC'] = mac.decode('utf8')
	message_dict['V_CODE'] = v_code
	message_dict['FILENAME'] = "fichero{}.txt".format(filename_counter)
	message_dict['CONTENT'] = {"a": 100, "b": "ewCkbS3QxUxdgPbmm62EYHiAA6izr22JnEkVdFagyKLmFki8SB2wjTXQJckxgtTWZCVBpEVwBKh54KzSz8YwZtchkDMXXDBCpLpTKYXMvT3qqqqqqqqqqqqqqqqqqqqqqqqq1"}

	filename_counter = filename_counter + 1
	return message_dict


This is the main loop, it consists only in keep listening to the environment,
and when green light is given, to send the data.

while (True):
	go_ahead = listen_receiver()
	if go_ahead == True:
		send_data_to_receiver(get_new_message_dict())
	gc.collect()
	time.sleep(1)
'''
gc.enable()
lora = LoRa(mode=LoRa.LORA, frequency=868000000, region=LoRa.EU868)
socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
socket.setblocking(False)

#Lora MAC
MAC = binascii.hexlify(network.LoRa().mac())

DEBUG = True

THREAD_EXIT = False
READ_NEW_LOG_FILE = True
log_file = None

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


def listen_receiver():
	global MAC
	global DEBUG

	data = socket.recv(256)
	print_rssi_quality_percentage()
	request_data_info_command = "MAC:::{};;;COMMAND:::{}".format(MAC.decode('utf-8'), 'request-data-info').encode()
	chunk_command = "MAC:::{};;;COMMAND:::{}".format(MAC.decode('utf-8'), 'chunk-').encode()
	print('LISTEN_RECEIVER() || received_content', data)
	print("my mac:", MAC.decode('utf-8'))

	if data.startswith(request_data_info_command):
		print("rdi")
		handle_command(data, "request-data-info") #TODO Sacar a variable global los String de comandos
	elif data.startswith(chunk_command):
		print("c")
		handle_command(data, "chunk-")


def read_datalogger():
	global THREAD_EXIT
	global READ_NEW_LOG_FILE
	global log_file

	file_counter = 0
	while (True):
		if THREAD_EXIT == True:
			break

		if READ_NEW_LOG_FILE == True:
			print("new log_file")
			log_file = File("{}.txt".format(file_counter),
							'{"a": 100, "b": "ewCkbS3QxUxdgPbmm62EYHiAA6izr22JnEkVdFagyKLmFki8SB2wjTXQJckxgtTWZCVBpEVwBKh54KzSz8YwZtchkDMXXDBCpLpTKYXMvT3qqqqqqqqqqqqqqqqqqqqqqqqq1", "tercera": "xxxa98sx79a8s7x998a7sf98u7a9ufy9ahvizuxyvkjxuivhkjwhvuisdhkjhviuxhkvuishvkhsdhjvxc"}'.encode(),
							200)
			READ_NEW_LOG_FILE = False
		file_counter += 1
		time.sleep(5)


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
