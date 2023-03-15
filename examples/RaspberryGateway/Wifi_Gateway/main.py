from AlLoRa.Nodes.Gateway import Gateway
from AlLoRa.Connectors.Wifi_connector import WiFi_connector
from AlLoRa.Digital_Endpoint import Digital_Endpoint


if __name__ == "__main__":
    # First, let's set access to LoRa through a WiFi Connector and its adapter
    connector = WiFi_connector(RECEIVER_API_HOST = "192.168.4.1", RECEIVER_API_PORT = 80)

    # Set up the Gateway Node with the connector, we will focus 10 seconds at a time per Node...
    lora_gateway = Gateway(connector = connector, config_file = "LoRa.json",
                            debug_hops = False, TIME_PER_ENDPOINT = 10)

    # Listen to the digital_endpoints and print and save the files as they come in
    lora_gateway.check_digital_endpoints(print_file_content=True, save_files=True)   

