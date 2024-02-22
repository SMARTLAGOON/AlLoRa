import time, sys, gc, ujson
import os
import _thread

from lora32 import T3S3
from utils.sd_manager import SD_manager
from utils.oled_screen import OLED_Screen
from utils.led_alive import LED

from AlLoRa.Nodes.Source import Source
from AlLoRa.Connectors.SX127x_connector import SX127x_connector

gc.enable()

# Function to access SD data and send it through AlLoRa
def get_oldest_SD_file(sd):
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
        ctp_file = CTP_File(name=filename, content=file, chunk_size=self.get_file_chunk_size())
        return ctp_file
    except Exception as e:
        print("Error getting file: ", e)
        return None


# Initialize T3S3 and SD_manager
t3s3 = T3S3()
sd_manager = SD_manager(sclk=t3s3.SD_SCLK, mosi=t3s3.SD_MOSI, miso=t3s3.SD_MISO, cs=t3s3.SD_CS)
# Initialize LED and OLED for status
led = LED(t3s3)

with open("AlLoRa.json", "r") as f:
    img_data = ujson.load(f)
screen = OLED_Screen(t3s3, img_data, "AlLoRa", "F")
screen.show_in_screen("Wait", '') 

def run():
    # AlLoRa setup
    led.run()
    connector=SX127x_connector()
    lora_node = Source(connector, config_file="LoRa_source.json")
    chunk_size = lora_node.get_chunk_size() #235
    
    print("CURRENT: ",sd_manager.get_files())
    print("PATH: ", sd_manager.get_path())
    
    try:
        lora_node.establish_connection()
        print("Connection OK")
        screen.show_in_screen("OK!", '') 
        while gpsDatasource.is_started():
            if not lora_node.got_file():
                file = get_oldest_SD_file(sd_manager)
                if file is not None:
                    print("Sending LoRa file: ", file.get_name())
                    screen.show_in_screen("Sending", file.get_name()) 
                    lora_node.set_file(file)
                    lora_node.send_file()
                    screen.show_in_screen("Sent", file.get_name()) 
                    gpsDatasource.erase_file(file.get_name())
            time.sleep(10)

    except Exception as e:
        print(e)
        screen.show_in_screen("Error", e)
        gpsDatasource.stop()
        print("NEW FILES: ", sd_manager.get_files())
        sd_manager.unmount()
        led.kill()
    print("EXIT")

run()



