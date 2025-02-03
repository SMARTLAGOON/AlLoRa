# Source Nodes examples

This folder contains the code for enabling different devices as Source Nodes. 

There are tree main files in this folder:

- **main.py**: This file contains a simple example of how to use the AlLoRa library to send files to a Requester Node. The Source Node generates files with random content and sends them to the Requester Node. 
  
- **main_pro.py**: This file contains a more complex example of how to use the AlLoRa library to send files to a Requester Node. It takes advantage of the device's hardware, and uses the screen and the SD card reader. It uses the screen of the device to display the status of the communication and the files being sent. The files to be sent are accessed from the SD card reader. This example can provide a deeper understanding of how to use the AlLoRa library and the device's hardware on a real-world application.
  
- **LoRa.json**: This file contains the configuration for the LoRa module. It is used by the AlLoRa library to configure the LoRa module. You should be sure to have both the Source and the Requester/Gateway node with the same LoRa configuration in order to establish a proper communication between them.
