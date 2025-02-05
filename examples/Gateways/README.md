# Gateway examples: 

This folder contains the code for enabling a device as a Gateway Node. 
We are asuming that the device doesn't have a LoRa module, so it will use an adapter to connect to the LoRa module. 
The Serial Gateway has been developed for the Raspberry Pi, but it can be adapted to other devices with UART capabilities. 
The Wifi GAteway has been tested both in Raspberry Pi and Linux/MacOS devices connected to the same network or to the WiFi Adapter's hotspot.

There are tree main files in each folder:

- **main.py**: This file contains a simple example of how to use the AlLoRa library to poll different Source Nodes. The Gateway Node sends commands to the Source Nodes and waits for the response. 
- **LoRa.json**: This file contains the configuration for the Connector module. It is used by the AlLoRa library to configure the Connector module. You should be sure to have both the Source and the Gateway node with the same LoRa configuration in order to establish a proper communication between them.
- **Nodes.json**: This file contains the configuration for the Source Nodes. It is used by the AlLoRa library to configure the Digital Endpoint for each Source Node. Each Source Node must be registered and be active in order to be polled by the Gateway Node. Different Source Nodes can have different LoRa configurations, and the Node will adjust its Connector configuration to match the Source Node's configuration.