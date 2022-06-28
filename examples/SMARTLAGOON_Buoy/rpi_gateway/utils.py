import json
import logging.handlers
import os
import time
from configparser import ConfigParser

logger_info = logging.getLogger('info')
logger_info.setLevel(logging.INFO)
logger_debug = logging.getLogger('debug')
logger_debug.setLevel(logging.DEBUG)
logger_error = logging.getLogger('error')
logger_error.setLevel(logging.ERROR)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - PROCESS( %(process)d ) FILENAME( %(filename)s ) LINE( %(lineno)s ) MESSAGE( %(message)s )')

current_path = os.path.dirname(__file__)
try:
    os.mkdir('logs')
except Exception as e:
    pass

full_absolute_path = os.path.join(current_path, './logs/{}.log'.format(time.strftime("%Y-%m-%d_%H:%M:%S")))

handler = logging.handlers.RotatingFileHandler(full_absolute_path, maxBytes=5242880, backupCount=100)
handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

#logger_info.addHandler(console_handler)
#logger_debug.addHandler(console_handler)
#logger_error.addHandler(console_handler)

#logger_info.addHandler(handler)
#logger_debug.addHandler(handler)
#logger_error.addHandler(handler)

RECEIVER_MAC_ADDRESS = ""
RECEIVER_API_HOST = "192.168.4.1"
RECEIVER_API_PORT = 80
SOCKET_TIMEOUT = 10
PACKET_RETRY_SLEEP = 5
SOCKET_RECV_SIZE = 10000
SYNC_REMOTE_FILE_SENDING_TIME_SLEEP = 1
SYNC_REMOTE_FILE_SENDING_MAX_RETRIES = 10
NEXT_ACTION_TIME_SLEEP = 1
SYNC_REMOTE_DIRECTORY_UPDATE_INTERVAL_SECONDS = 1

BUOYS = list()


def load_config():
    global RECEIVER_MAC_ADDRESS
    global RECEIVER_API_HOST
    global RECEIVER_API_PORT
    global SOCKET_TIMEOUT
    global PACKET_RETRY_SLEEP
    global SOCKET_RECV_SIZE
    
    global SYNC_REMOTE
    global SYNC_REMOTE_FILE_SENDING_TIME_SLEEP
    global SYNC_REMOTE_FILE_SENDING_MAX_RETRIES
    global NEXT_ACTION_TIME_SLEEP
    global SYNC_REMOTE_DIRECTORY_UPDATE_INTERVAL_SECONDS
    global TIME_PER_BUOY
    global MAX_RETRANSMISSIONS_BEFORE_MESH

    logger_info.info("Loading config")

    config = ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), './config.ini'))

    RECEIVER_MAC_ADDRESS = config.get('receiver', 'RECEIVER_MAC_ADDRESS')
    RECEIVER_API_HOST = config.get('receiver', 'RECEIVER_API_HOST')
    RECEIVER_API_PORT = config.getint('receiver', 'RECEIVER_API_PORT')
    SOCKET_TIMEOUT = config.getint('receiver', 'SOCKET_TIMEOUT')
    PACKET_RETRY_SLEEP = config.getfloat('receiver', 'PACKET_RETRY_SLEEP')
    SOCKET_RECV_SIZE = config.getint('receiver', 'SOCKET_RECV_SIZE')
    
    SYNC_REMOTE = config.getboolean('general', 'SYNC_REMOTE')
    SYNC_REMOTE_FILE_SENDING_TIME_SLEEP = config.getint('general', 'SYNC_REMOTE_FILE_SENDING_TIME_SLEEP')
    SYNC_REMOTE_FILE_SENDING_MAX_RETRIES = config.getint('general', 'SYNC_REMOTE_FILE_SENDING_MAX_RETRIES')
    NEXT_ACTION_TIME_SLEEP = config.getfloat('general', 'NEXT_ACTION_TIME_SLEEP')
    SYNC_REMOTE_DIRECTORY_UPDATE_INTERVAL_SECONDS = config.getfloat('general', 'SYNC_REMOTE_DIRECTORY_UPDATE_INTERVAL_SECONDS')
    TIME_PER_BUOY = config.getint('general', 'TIME_PER_BUOY')
    MAX_RETRANSMISSIONS_BEFORE_MESH = config.getint('general', 'MAX_RETRANSMISSIONS_BEFORE_MESH')


def load_buoys_json():
    with open('./buoy-list.json', 'r') as fp:
        buoys_json = json.loads(fp.read())
        return buoys_json
