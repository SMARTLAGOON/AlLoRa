from AlLoRa.Nodes.Gateway import Gateway
from AlLoRa.Connectors.Wifi_connector import WiFi_connector

config_file = "LoRa.json"
node_file = "Nodes.json"
if __name__ == "__main__":
    # First, let's set access to LoRa through a WiFi Connector and its adapter
    connector = WiFi_connector()

    # Set up the Gateway Node with the connector, we will focus 10 seconds at a time per Node...
    lora_gateway = Gateway(connector = connector, config_file = config_file,
                            debug_hops = False)
    # Listen to the digital_endpoints and print and save the files as they come in
    lora_gateway.check_digital_endpoints(print_file_content=True, save_files=True)   

