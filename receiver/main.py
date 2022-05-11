import usocket
import _thread
import time
from network import WLAN
import pycom
import lora_handler
import gc
import ujson

#Enable garbage collector
gc.enable()

#Thread exit flag
THREAD_EXIT = False

#Debug flag
DEBUG = False

'''
This function runs an HTTP API that serves as a LoRa forwarder for the rpi_receiver that connects to it
'''
def client_thread(clientsocket):
	try:
		global DEBUG

		r = clientsocket.recv(256) #MERGE

		# If recv() returns with 0 the other end closed the connection
		if len(r) == 0:
		    clientsocket.close()
		    return
		else:
		    if DEBUG == True:
		    	print("Received: {}".format(str(r)))

		http = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection:close \r\n\r\n" #HTTP response

		if "POST /send-command "in str(r):
			response_json = ujson.loads(str(r).split("\\r\\n\\r\\n")[1][:-1]) #FIXME A comma from nowhere is sneaked into it, that is why I use slicing.

			#Response to the sender (buoy)
			buoy_response = lora_handler.send_command(response_json['command'], response_json['buoy_mac_address'])

			json_buoy_response = ujson.dumps({"command_response": buoy_response})
			if DEBUG == True:
				print("HTTP", json_buoy_response)
			clientsocket.send(http + json_buoy_response)
	except Exception as e:
		print(e)
	# Close the socket and terminate the thread
	clientsocket.close()


wlan = WLAN()
wlan.init(mode=WLAN.AP, ssid="smartlagoon_land_receiver", auth=(WLAN.WPA2, "smartlagoonX98ASasd00de2l"))
#print(wlan.ifconfig(id=1)) #id =1 signifies the AP interface
time.sleep(1)

# Set up server socket
serversocket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
serversocket.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
serversocket.bind(("192.168.4.1", 80))

# Accept maximum of 1 connection at the same time.
serversocket.listen(1)

#We only need one connection thread since it is just an rpi_receiver connected, plus, otherwise also threading memory problems may arise, so, as a preventive fix, threading was removed.
while True:
	try:
		if THREAD_EXIT is True:
			break
		# Accept the connection of the clients
		(clientsocket, address) = serversocket.accept()
		clientsocket.settimeout(0) #MERGE
		gc.collect()
		client_thread(clientsocket)
	except KeyboardInterrupt as e:
		THREAD_EXIT = True
		print("THREAD_EXIT")
serversocket.close()
