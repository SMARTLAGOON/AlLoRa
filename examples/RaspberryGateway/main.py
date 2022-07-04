from m3LoRaCTP.Nodes.Gateway_Node import m3LoRaCTP_Gateway
from m3LoRaCTP.Connectors.Wifi_connector import WiFi_connector
from m3LoRaCTP.Digital_Endpoint import Digital_EndPoint


if __name__ == "__main__":
    # First, let's set access to LoRa through a WiFi Connector and its adapter
    connector = WiFi_connector(RECEIVER_API_HOST = "192.168.4.1", RECEIVER_API_PORT = 80)

    # Set up the Gateway Node with the connector, we will focus 10 seconds at a time per Node...
    lora_gateway = m3LoRaCTP_Gateway(mesh_mode = True, debug_hops = False, 
                                        connector = connector, TIME_PER_ENDPOINT = 10)

    # Setting some Sender  Nodes to listen...
    node_nickname = "A"
    node_mac_address = "70b3d5499a76ba3f"
    node_a = Digital_EndPoint(name=node_nickname, mac_address = node_mac_address, active = True)
    
    node_nickname = "C"
    node_mac_address = "70b3d549922f4240"
    node_c = Digital_EndPoint(name=node_nickname, mac_address = node_mac_address, active = True)

    
    digital_endpoints = [node_a, node_c]                    # Put them into a list
    lora_gateway.set_digital_endpoints(digital_endpoints)   # Give them to the gateway

    print("Listening to endpoints!")
    lora_gateway.check_digital_endpoints(print_file_content=True)   # Use this to listen to them...
                                                                    # print_file_content = True to check 
                                                                    # responses when completed...

