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
DEBUG = False

#Thread exit flag
THREAD_EXIT = False

#datalogger mockup
READ_NEW_LOG_FILE = False	# Antes era True, pero probar a enviar solo si pide algo...
log_file = None

# For testing
sizes = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
sfs = [7, 8, 9, 10, 11, 12]		# For changing SF in sync with the receiver
len_list = len(sizes)
file_counter = 0
chunk_size = 200	# Variable

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

	global file_counter
	global chunk_size

	response = None
	if type == "request-data-info":
		if log_file:
			if log_file.first_sent and not log_file.last_sent:	# If some chunks are already sent...
				t_file(log_file, False)	# Take this as a final ack for last package
				log_file = read_file(file_counter, chunk_size)	#generate_file
				file_counter += 1
			else:
				log_file.retransmission += 1
				if DEBUG == True:
					print("asked again for data_info")
			#if not, continue trying to send first packet of the file
		else:	# For the first file
			log_file = read_file(file_counter, chunk_size)	#generate_file
			file_counter += 1

		#READ_NEW_LOG_FILE = True #It allows to load the next one
		response = "MAC:::{};;;LENGTH:::{};;;FILENAME:::{}".format(MAC.decode('utf-8'), log_file.get_length(), log_file.get_name()).encode()

	elif type == "chunk-":
		requested_chunk = int(command.decode('utf-8').split(";;;")[1].split(":::")[1].split('-')[1])
		if DEBUG == True:
			print("RC: {}".format(requested_chunk))
		response = "MAC:::{};;;CHUNK:::{}".format(MAC.decode('utf-8'), log_file.get_chunk(requested_chunk)).encode()
		if not log_file.first_sent:
			t_file(log_file, True)	# Reading new file
			#pycom.rgbled(0x007f00) # green
			#time.sleep(1)
			#pycom.rgbled(0x000000)

	socket.send(response)


'''
This function ensures that a received message matches the criteria of any expected message.
'''
def listen_receiver():
	global MAC
	global DEBUG

	data = socket.recv(256)
	if DEBUG == True:
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
	if DEBUG == True:
		print(json)
	file = File('{}.json'.format(file_counter), json, 200)
	return file

# For testing
def read_file(file_counter, chunk_size):
	global DEBUG
	global sizes
	global len_list
	n = file_counter%len_list
	size = sizes[n]

	#f = open('files/file_{}kb'.format(size))
	content = ''
	gc.collect()
	content = '{}'.format(n%10)*(1024 * size)
	#content = f.read()
	#f.close()
	if DEBUG == True:
		print("Going to send {} kb file...".format(size))
	file = File('{}.json'.format(size), content, chunk_size)
	#print("150kb")
	return file

def t_file(file, t0_tf):
	file_name = file.get_name()
	t = time.time()
	if DEBUG == True:
		print("SAVING!")
	test_log = open('log.txt', "ab")
	if t0_tf:
		file.first_sent = t
		txt = "{};t0;{};".format(file.get_name(), t)
		test_log.write(txt)
		print(txt)
	else:
		if file.first_sent is not None:
			file.last_sent = t
			txt = "tf;{};SST;{};Retransmission;{};[{}]\n".format(t, t - file.first_sent, file.retransmission, file.get_name())
			test_log.write(txt)
			if DEBUG == True:
				print(txt)
	test_log.close()
	return t

def clean_t_file():
	test_log = open('log.txt', "wb")
	test_log.write("")
	test_log.close()



'''
This function mocks up an existing datalogger
'''
def read_datalogger():
	global THREAD_EXIT
	global READ_NEW_LOG_FILE
	global log_file
	global DEBUG

	file_counter = 0
	chunk_size = 200	# Variable
	while (True):
		if THREAD_EXIT == True:
			break

		if READ_NEW_LOG_FILE == True:
			if DEBUG == True:
				print("new log_file")
			log_file = read_file(file_counter, chunk_size)	#generate_file
			READ_NEW_LOG_FILE = False

			file_counter += 1
		#time.sleep(60)	# Esto estaba molestando muchas cosas




'''
This function starts the datalogger mockup and keeps a loop waiting for messages.
'''
if __name__ == "__main__":
	clean_t_file()	#Dangerous!
	#_thread.start_new_thread(read_datalogger, ())
	try:
		while (True):
			listen_receiver()
			gc.collect()
			#time.sleep(1)		# Bajar este tiempo
	except KeyboardInterrupt as e:
		print("THREAD_EXIT")
		THREAD_EXIT = True
