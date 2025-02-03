# Requester Node examples

This folder contains the code for enabling different devices as Requester Nodes. 

Similar to the Source Nodes, the Requester Nodes have three main files:

- **main.py**: This file contains a simple example of how to use the AlLoRa library to receive files from a Source Node. The Requester Node waits for files to be sent by the Source Node and saves them to the device's memory.
  
- **main_pro.py**: This file contains a more complex example of how to use the AlLoRa library to receive files from a Source Node. It takes advantage of the device's hardware, and uses the screen and the SD card reader. It uses the screen of the device to display the status of the communication and the files being received. The files received are saved to the SD card reader. This example can provide a deeper understanding of how to use the AlLoRa library and the device's hardware on a real-world application.

- **LoRa.json**: This file contains the configuration for the LoRa module. It is used by the AlLoRa library to configure the LoRa module. You should be sure to have both the Source and the Requester node with the same LoRa configuration in order to establish a proper communication between them.


In order to poll the respective Source Node, the Requester Node must register the Source Node's MAC address. This is done by setting the `node_mac_address` variable in the Requester's main.py file. The MAC address can be found in the console when the Source Node boots up.

Each Source Node to be polled will be represented by its own instance of a Digital Endpoint (check line 18 in [main.py](https://github.com/SMARTLAGOON/AlLoRa/blob/8522aafe2544122a59fb7bb9058fa5dd9e490c30/examples/Requesters/T3S3/main.py)). The Digital Endpoint is a class that represents the Source Node and is responsible for managing the status of the communication with the Source Node. It is also responsible for managing the files received from the Source Node in the Requester's side. 