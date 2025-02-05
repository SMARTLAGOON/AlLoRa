# T3S3 Source Node

This folder contains the code for enabling a T3S3 device as a Source Node. 
There are two main files in this folder:

- **main.py**: This file contains a simple example of how to use the AlLoRa library to send files to a Requester Node. The Source Node generates files with random content and sends them to the Requester Node. This is the one used in the example described in the [Readme from the examples folder](https://github.com/SMARTLAGOON/AlLoRa/blob/9dbf80c2df2a20b56b88fc92a0045e79c19862b3/examples/Readme.md).
- **main_pro.py**: This file contains a more complex example of how to use the AlLoRa library to send files to a Requester Node. It takes advantage of the T3S3's hardware, and uses the screen and the SD card reader. It uses the screen of the T3S3 to display the status of the communication and the files being sent. The files to be sent are accessed from the SD card reader. This example can provide a deeper understanding of how to use the AlLoRa library and the T3S3's hardware on a real-world application.
- **LoRa.json**: This file contains the configuration for the LoRa module. It is used by the AlLoRa library to configure the LoRa module. You should be sure to have both the Source and the Requester/Gateway node with the same LoRa configuration in order to establish a proper communication between them.