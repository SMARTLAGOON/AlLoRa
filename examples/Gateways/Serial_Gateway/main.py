import RPi.GPIO as GPIO
import time
import  sys, gc

from AlLoRa.Nodes.Gateway import Gateway
from AlLoRa.Connectors.Serial_connector import Serial_connector


def reset_esp32():
    RST_PIN = 23  # Or load from configuration
    GPIO.setmode(GPIO.BCM)
    
    try:
        GPIO.setup(RST_PIN, GPIO.OUT)
    except RuntimeError:
        GPIO.cleanup(RST_PIN)  # Cleanup the specific pin if setup fails
        GPIO.setup(RST_PIN, GPIO.OUT)  # Retry setup after cleanup

    GPIO.output(RST_PIN, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(RST_PIN, GPIO.HIGH)
    print("ESP32 has been reset.")
    GPIO.cleanup()


if __name__ == "__main__":
    reset_esp32()     
    connector = Serial_connector(reset_function=reset_esp32)
    allora_gateway = Gateway(connector, config_file= "LoRa.json", debug_hops= False)
    # Listen to the digital_endpoints and print and save the files as they come in
    allora_gateway.check_digital_endpoints(print_file_content = True, save_files = True)