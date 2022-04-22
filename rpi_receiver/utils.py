import json
import logging.handlers
import os
import socket
import time
import select
from configparser import ConfigParser


logger_info = logging.getLogger('info')
logger_info.setLevel(logging.INFO)
logger_debug = logging.getLogger('debug')
logger_debug.setLevel(logging.DEBUG)
logger_error = logging.getLogger('error')
logger_error.setLevel(logging.ERROR)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - PROCESS( %(process)d ) FILENAME( %(filename)s ) LINE( %(lineno)s ) MESSAGE( %(message)s )')

try:
    os.mkdir('logs')
except Exception as e:
    pass

current_path = os.path.dirname(__file__)
full_absolute_path = os.path.join(current_path, './logs/{}.log'.format(time.strftime("%Y-%m-%d_%H:%M:%S")))

handler = logging.handlers.RotatingFileHandler(full_absolute_path, maxBytes=5242880, backupCount=100)
handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger_info.addHandler(console_handler)
#logger_debug.addHandler(console_handler)
logger_error.addHandler(console_handler)

logger_info.addHandler(handler)
logger_debug.addHandler(handler)
logger_error.addHandler(handler)


RECEIVER_API_HOST = "192.168.4.1"
RECEIVER_API_PORT = 80
SOCKET_TIMEOUT = 10
COMMAND_RETRY_SLEEP = 5
SOCKET_RECV_SIZE = 10000
SYNC_REMOTE_FILE_SENDING_TIME_SLEEP = 1
SYNC_REMOTE_FILE_SENDING_MAX_RETRIES = 10
NEXT_ACTION_TIME_SLEEP = 1
SYNC_REMOTE_DIRECTORY_UPDATE_INTERVAL_SECONDS = 1


def load_config():
    global RECEIVER_API_HOST
    global RECEIVER_API_PORT
    global SOCKET_TIMEOUT
    global COMMAND_RETRY_SLEEP
    global SOCKET_RECV_SIZE
    global SYNC_REMOTE_FILE_SENDING_TIME_SLEEP
    global SYNC_REMOTE_FILE_SENDING_MAX_RETRIES
    global NEXT_ACTION_TIME_SLEEP
    global SYNC_REMOTE_DIRECTORY_UPDATE_INTERVAL_SECONDS

    logger_info.info("Loading config")

    config = ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), './config.ini'))

    RECEIVER_API_HOST = config.get('receiver', 'RECEIVER_API_HOST')
    RECEIVER_API_PORT = config.getint('receiver', 'RECEIVER_API_PORT')
    SOCKET_TIMEOUT = config.getint('receiver', 'SOCKET_TIMEOUT')
    COMMAND_RETRY_SLEEP = config.getint('receiver', 'COMMAND_RETRY_SLEEP')
    SOCKET_RECV_SIZE = config.getint('receiver', 'SOCKET_RECV_SIZE')
    SYNC_REMOTE_FILE_SENDING_TIME_SLEEP = config.getint('general', 'SYNC_REMOTE_FILE_SENDING_TIME_SLEEP')
    SYNC_REMOTE_FILE_SENDING_MAX_RETRIES = config.getint('general', 'SYNC_REMOTE_FILE_SENDING_MAX_RETRIES')
    NEXT_ACTION_TIME_SLEEP = config.getfloat('general', 'NEXT_ACTION_TIME_SLEEP')
    SYNC_REMOTE_DIRECTORY_UPDATE_INTERVAL_SECONDS = config.getfloat('general', 'SYNC_REMOTE_DIRECTORY_UPDATE_INTERVAL_SECONDS')


def load_buoys_json():
    with open('./buoy-list.json', 'r') as fp:
        buoys_json = json.loads(fp.read())
        return buoys_json


'''
This function carries out all the communication with receiver's HTTP API.

Disclaimer: Using Python Requests was unsuccessful. I still do not know why.
'''
def send_command(command: str, buoy):
    global RECEIVER_API_HOST
    global RECEIVER_API_PORT
    global SOCKET_TIMEOUT
    global COMMAND_RETRY_SLEEP
    global SOCKET_RECV_SIZE

    json_response = None
    retry = True
    while retry is True:
        try:
            s = socket.socket()
            s.setblocking(True)
            addr = socket.getaddrinfo(RECEIVER_API_HOST, RECEIVER_API_PORT)[0][-1]
            s.settimeout(SOCKET_TIMEOUT)
            s.connect(addr)


            content = json.dumps({"command": command,
                                  "buoy_mac_address": buoy.get_mac_address()})

            httpreq = 'POST {} HTTP/1.1\r\nHost: {}\r\nConnection: close\r\nAccept: */*\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\r\n{}'.format(
                "/send-command", RECEIVER_API_HOST, len(content), content).encode('utf-8')


            ready_to_read, ready_to_write, in_error = select.select([],
                                                                    [s],
                                                                    [],
                                                                    15)
            s.send(httpreq)
            ready_to_read, ready_to_write, in_error = select.select([s],
                                                                    [],
                                                                    [s],
                                                                    15)
            response = s.recv(SOCKET_RECV_SIZE)

            retry = False
            extracted_response = response.decode('utf-8').split('\r\n\r\n')[1]
            json_response = json.loads(extracted_response)
        except Exception as e:
            logger_error.error("Buoy {} Allowed Exception (Network connection was interrupted by some reason, but will keep trying to reconnect): {}".format(buoy.get_name(), e))
            time.sleep(COMMAND_RETRY_SLEEP)
            retry = True
    return json_response['command_response']

