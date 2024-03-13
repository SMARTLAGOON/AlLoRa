import time, sys, gc, ujson
import os
import _thread

from lora32 import T3S3
from utils.sd_manager import SD_manager
from utils.oled_screen import OLED_Screen
from utils.led_alive import LED

from AlLoRa.Nodes.Requester import Requester
from AlLoRa.Connectors.SX127x_connector import SX127x_connector
from AlLoRa.Digital_Endpoint import Digital_Endpoint

# Initialize T3S3 and SD_manager
t3s3 = T3S3()
sd_manager = SD_manager(sclk=t3s3.SD_SCLK, mosi=t3s3.SD_MOSI, miso=t3s3.SD_MISO, cs=t3s3.SD_CS)
# Initialize LED and OLED for status
led = LED(t3s3)

with open("AlLoRa.json", "r") as f:
    img_data = ujson.load(f)
screen = OLED_Screen(t3s3, img_data, "AlLoRa", "R")
screen.show_in_screen("Wait", '') 

gc.enable()
if __name__ == "__main__":
    # First, we set the connector (basyc LoRa-LoPy connection to access to the LoPy's LoRa libraries)
    connector = SX127x_connector()
    # Then, we set up out Requester Node:
    lora_node = Requester(connector, config_file = "LoRa.json")

    # Here we setup a digital_endpoint to manage the connection to the Node
    node_nickname = "T"
    node_mac_address = "75dbb280" # Replace with the MAC address of the node you want to connect to
    node_a = Digital_Endpoint(name=node_nickname, mac_address = node_mac_address, active = True)

    # In this loop we listen to the endpoint until we have a complete file and print it.. (just for testing purposes)
    print("Starting listening to {}".format(node_mac_address))
    screen.show_in_screen("Listening", node_mac_address)
    while True:
        file = None
        while file==None:
            file = lora_node.listen_to_endpoint(node_a, 100, print_file=True)
        file_content = file.get_content()
        # Save file to SD
        sd_manager.create_file(file.get_name(), file_content)
        gc.collect()
        time.sleep(10)