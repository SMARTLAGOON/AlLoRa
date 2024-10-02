import utime, sys, gc, ujson, machine
import os
import _thread

from lora32 import T3S3
from utils.sd_manager import SD_manager
from utils.oled_screen import OLED_Screen
from utils.led_alive import LED
from subslogger import Logger

from AlLoRa.Nodes.Source import Source
from AlLoRa.Connectors.SX127x_connector import SX127x_connector
from AlLoRa.File import CTP_File

gc.enable()

# Function to access SD data and send it through AlLoRa
def get_oldest_SD_file(sd, chunk_size):
    files = sd.get_files()
    if not files:
        return None
    ## Remove files inside the temp folder
    files = [file for file in files if not file.startswith("temp")]
    ## Remove from list all files that start with a "."
    files = [file for file in files if not file.startswith(".")]
    if not files:
        return None
    ## Sort files by name
    try:
        files.sort()
        print(files)
        oldest_file_name = files[0]
        print(oldest_file_name)
        file = sd.get_file(oldest_file_name)
        filename = file.filename.split("/")[-1]
        print("Getting file: ", filename, " from SD", file)
        ctp_file = CTP_File(name=filename, content=file, chunk_size=chunk_size)
        return ctp_file
    except Exception as e:
        print("Error getting file: ", e)
        return None


# Initialize T3S3 and SD_manager
device = T3S3()
#led = LED(device)
#led.run()

# print("CURRENT: ",sd_manager.get_files())
# print("PATH: ", sd_manager.get_path())

source_layout = [
    {'key': 'MAC', 'pos': {'x': 40, 'y': 0}, 'area': {'x': 40, 'y': 0, 'w': 88, 'h': 12}, 'static': True},
    # {'key': 'File', 'pos': {'x': 40, 'y': 12}, 'area': {'x': 40, 'y': 12, 'w': 88, 'h': 12}},
    {'key': "BW", 'pos': {'x': 40, 'y': 12}, 'area': {'x': 40, 'y': 12, 'w': 30, 'h': 12}},
    {'key': "TX_P", 'pos': {'x': 70, 'y': 12}, 'area': {'x': 70, 'y': 12, 'w': 25, 'h': 12}},
    {'key': "SNR", 'pos': {'x': 95, 'y': 12}, 'area': {'x': 95, 'y': 12, 'w': 30, 'h': 12}},
    {'key': 'RSSI', 'pos': {'x': 40, 'y': 24}, 'area': {'x': 40, 'y': 24, 'w':40, 'h': 12}},
    {'key': 'Chunk', 'pos': {'x': 80, 'y': 24}, 'area': {'x': 80, 'y': 24, 'w': 30, 'h': 12}}, 
    {'key': 'SF', 'pos': {'x': 110, 'y': 24}, 'area': {'x': 110, 'y': 24, 'w': 30, 'h': 12}},
]

with open("AlLoRa_logo.json", "r") as f:
    img_data = ujson.load(f)

screen = OLED_Screen(device, img_data, layout_config=source_layout, button=False)

# print("CURRENT: ",sd_manager.get_files())
# print("PATH: ", sd_manager.get_path())
    

def run():
    # AlLoRa setup
    connector = SX127x_connector()
    lora_node = Source(connector, config_file="LoRa.json")
    # lora_node.register_subscriber(screen)
    # lora_node.notify_subscribers()
    #lora_node.chunk_size = 235
    #chunk_size = lora_node.get_chunk_size() #235
    print("CHUNK SIZE: ", lora_node.chunk_size)
    sd_manager = SD_manager(sclk=device.SD_SCLK, mosi=device.SD_MOSI, miso=device.SD_MISO, cs=device.SD_CS)
    print("CURRENT: ",sd_manager.get_files())
    print("PATH: ", sd_manager.get_path())

    logger = Logger(
    always_log_topics=["RSSI", "SNR", "Chunk", "PSizeS", "PSizeR", "TimePR", 'TimePS', 'TimeBtw'],
    change_log_topics=["File", "Status", "Retransmission", "CorruptedPackets", "Freq", "SF", "BW", "CR", "TX_P"]
    )

    lora_node.register_subscriber(screen)
    lora_node.register_subscriber(logger)
    lora_node.notify_subscribers()
    
    sending_timeout = 2 * 60 * 1000 # 2 minutes in milliseconds
    t0 = utime.ticks_ms()
    try:
        lora_node.establish_connection()
        print("Connection OK")
        while sd_manager.get_files():
            if not lora_node.got_file():
                file = get_oldest_SD_file(sd_manager, lora_node.chunk_size)
                if file is not None:
                    print("Sending LoRa file: ", file.get_name())
                    lora_node.set_file(file)
                    t_0_send = utime.ticks_ms()
                    sucess = lora_node.send_file(timeout=sending_timeout)
                    if sucess:
                        td = utime.ticks_diff(utime.ticks_ms(), t_0_send)
                        if td > sending_timeout:
                            print("Timeout sending file")
                    else:
                        print("Error sending file")
                        machine.reset() # Reset device
                    #erase_file.erase_file(file.get_name())
            utime.sleep(10)

    except Exception as e:
        print(e)
        print("NEW FILES: ", sd_manager.get_files())
        sd_manager.unmount()
        #led.kill()
    print("EXIT")
    machine.reset() # Reset device

run()