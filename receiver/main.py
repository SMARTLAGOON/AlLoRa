import ujson
import time
import gc
import os
import wifi_dispatcher
import _thread
import pycom
from network import LoRa
import socket
from machine import Timer
from machine import WDT
'''
#We enable the Lora connection socket and garbage collector
gc.enable()
lora = LoRa(mode=LoRa.LORA, frequency=868000000, region=LoRa.EU868)
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

#Controls the polling time between buoy senders
WAIT_MAX_TIMEOUT = 30

#Controls the number of program cycles before WDT gets restarted
WDT_FEED_WAITING_ITERATIONS = 300
DEBUG = False


Manages the timeout given to every sender before passing to the next, unless a response was received.

def wait_sender_data(sender_mac):
	global WAIT_MAX_TIMEOUT
	global DEBUG

	timeout = WAIT_MAX_TIMEOUT
	received_data = b''

	while(timeout > 0):
		if DEBUG == True:
			print("WAIT_SENDER_DATA() || quedan {} segundos timeout ({})".format(timeout, sender_mac))
		received_data = s.recv(256)
		if DEBUG == True:
			print("WAIT_SENDER_DATA() || sender_reply: {}".format(received_data))
		if received_data.startswith(b'MAC:::'):
			source_mac_address = received_data.decode('utf-8').split(";;;")[0].split(":::")[1]
			if source_mac_address == sender_mac:
				received = True
				break
		time.sleep(1)
		timeout = timeout - 1

	return received_data


Sends to the current sender a petition requesting its data.
's.setblocking()' is set to False to allow 'wait_sender_data()' performing iterations without getting stuck reading socket.

def request_to_senders(sender_mac):
	s.setblocking(False)
	request = b'MAC:::{};;;COMMAND:::{}'.format(sender_mac, 'REQUESTING_DATA')
	if DEBUG == True:
		print("REQUEST_TO_SENDERS() || request: {}".format(request))
	s.send(request)
	return wait_sender_data(sender_mac)


Decodes the received data and pass it to the method mandated for doing it.

def save(received_data):
	#TODO Para solucionar el UnicodeError, quizás pueda llegar a ser bueno colocar un try con un formato
	source_mac_address = received_data.decode('utf-8').split(";;;")[0].split(":::")[1]
	filename = received_data.decode('utf-8').split(";;;")[2].split(":::")[1]
	content = received_data.decode('utf-8').split(";;;")[3].split(":::")[1]

	if DEBUG == True:
		print("SAVE() || sending_to_api: {}".format(filename))
	sent = wifi_dispatcher.send_to_api(source_mac_address, filename, content.encode())
	if sent == True:
		if DEBUG == True:
			print("SAVE() || sent_to_api")
	return sent


Sends a reply message to the sender when the data is succesfully saved in API.

def reply(received_data):
	global s

	received_data = received_data.decode('utf-8')
	source_reply_v_code = received_data.split(";;;")[1]
	s.setblocking(True)
	if DEBUG == True:
		print("REPLY() || sending_reply: {}".format(source_reply_v_code))
	s.send(source_reply_v_code)



This is the main block and consist in interating through the list of buoys' senders,
giving in each iteration a quantum of time where every sender can send its logged data.

RECEIVER: Give quantum time.
SENDER: Sends data.
RECEIVER: Sends data to Raspberry Pi's API.
RECEIVER: Replies to the SENDER its data has been saved.

When the WDT_FEED_WAITING_ITERATIONS variable reaches 0, WDT watchdog performs a reboot,
avoiding this way an hypothetical panic'ed core sudden dump.

while (True):
	for sender_mac in wifi_dispatcher.request_sender_mac_list():
		try:
			received_data = request_to_senders(sender_mac)
			if received_data.startswith(b'MAC:::'):
				sent = False
				while (sent == False):
					sent = save(received_data)
					time.sleep(1)
				reply(received_data)
		except Exception as e:
			if DEBUG == True:
				print(e)
	gc.collect()
	if WDT_FEED_WAITING_ITERATIONS <= 0:
		s.close()
		wdt = WDT(timeout=100)
		wdt.feed()
	WDT_FEED_WAITING_ITERATIONS = WDT_FEED_WAITING_ITERATIONS - 1
	if DEBUG == True:
		print("{} ITERATIONS TO RESTART".format(WDT_FEED_WAITING_ITERATIONS))

	time.sleep(1)
'''
#####################


import usocket
import _thread
import time
from network import WLAN
import pycom
import lora_handler
import gc

#We enable the Lora connection socket and garbage collector
gc.enable()

THREAD_EXIT = False

# Thread for handling a client
def client_thread(clientsocket):
    # Receive maxium of 12 bytes from the client
	r = clientsocket.recv(4096)

	# If recv() returns with 0 the other end closed the connection
	if len(r) == 0:
	    clientsocket.close()
	    return
	else:
	    # Do something wth the received data...
	    print("Received: {}".format(str(r))) #uncomment this line to view the HTTP request

	http = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection:close \r\n\r\n" #HTTP response

	if "GET / " in str(r):
	    #this is a get response for the page
	    # Sends back some data
	    clientsocket.send(http + "<html><body><h1> You are connection "+ str(n) + "</h1><br> Your browser will send multiple requests <br> <a href='/hello'> hello!</a><br><a href='/color'>change led color!</a></body></html>")
	elif "POST /send-command "in str(r):
		response_json = ujson.loads(str(r).split("\\r\\n\\r\\n")[1][:-1]) #FIXME Se cuela una comilla y no sé de dónde aún, por eso el Slice
		#print("Se envía por LoRa:", response_json)
		#Envío a la boya y respuesta. (ojo timeouts de sockets).
		buoy_response = lora_handler.send_command(response_json['command'], response_json['buoy_mac_address'])
		#print(buoy_response)
		#buoy_response = "MAC:::{};;;CHUNKS:::{};;;FILENAME:::{}".format("a1", 4, "0.txt")
		json_buoy_response = ujson.dumps({"command_response": buoy_response})
		print("HTTP", json_buoy_response)
		clientsocket.send(http + json_buoy_response)
	# Close the socket and terminate the thread
	clientsocket.close()

time.sleep(1)
wlan = WLAN()
wlan.init(mode=WLAN.AP, ssid="smartlagoon_land_receiver", auth=(WLAN.WPA2, "smartlagoonX98ASasd00de2l"))
#print(wlan.ifconfig(id=1)) #id =1 signifies the AP interface
time.sleep(1)

# Set up server socket
serversocket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
serversocket.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
serversocket.bind(("192.168.4.1", 80))

# Accept maximum of 5 connections at the same time
serversocket.listen(1)

# Unique data to send back
while True:
	try:
		if THREAD_EXIT is True:
			break
		# Accept the connection of the clients
		(clientsocket, address) = serversocket.accept()
		# Start a new thread to handle the client
		gc.collect()
		client_thread(clientsocket)
		#_thread.start_new_thread(client_thread, (clientsocket,))
	except KeyboardInterrupt as e:
		THREAD_EXIT = True
		print("THREAD_EXIT")
serversocket.close()
