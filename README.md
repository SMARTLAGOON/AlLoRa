# BuoySoftware
This repo contains the software to send data from the SMARTLAGOON buoy to a server. It is a scalable LoRa based protocol.

## Purposes
Having a buoy placed on a lagoon, the sending part which is composed by one Pycom Lopy 4 over Pybytes board is connected inside it, along with a commercial datalogger (SENDER).

In the shore another Pycom Lopy 4 (RECEIVER) attached to one Raspberry Pi (rpi_receiver) along with its corresponding node, are placed. It handles and processes the received data.

## How does it work?
Many things happen at the same time, let us break it down.

### Sender
The sender has a non-ending loop looking for new data from the datalogger, which are intended to be collected through its Ethernet port, perhaps accessing in standalone mode to its API (under development).

It also has another non-ending loop awaiting for those data to be requested over LoRa by the receiver.

### Receiver
The receiver runs an HTTP API which serves as a LoRa dispatcher between buoy senders and rpi_receiver. It broadcasts over LoRa all the commands that rpi_receiver sends to its HTTP API. In other words, the receiver acts as a LoRa capabilities access intermediary for the rpi_receiver.

Receiver opens a Wi-Fi hotspot for the rpi_receiver to get connected in.

### Rpi_receiver
The rpi_receiver gets connected to the receiver's Wi-Fi hotspot. It holds all the communicating logic. It runs a simplistic protocol where all the senders are iterated for being requested for its new data.
The protocol messages are exchanged in this way:


(*) {} means a gap to be filled with concrete information.

"MAC:::{};;;COMMAND:::request-data-info" is sent to receiver over HTTP and receiver forwards over LoRa the same message; sender checks if MAC matches with its own MAC and sends a reply backwards; receiver re-checks whether MAC matches and sends back the sender's reply to rpi_receiver. This reply contains some metadata info about the data itself such as filename, number of chunks that make up the whole file and so on.

Once the rpi_receiver knows those metadata, it elaborates a bunch of requests until all the chunks are received. This requests are sent in the same way as the previous ones are. The subsequent requests meet this format "MAC:::{};;;COMMAND:::chunk-{}".

When rpi_receiver has finished fetching all the chunks, it reassembles and saves the data file and the process starts over.

## Running an example
The project structure is divided in three folders:

__sender:__ Pycom Lopy 4 code for buoy side.

__receiver:__ Pycom Lopy 4 code for land side.

__rpi_receiver:__ Raspberry Pi code for land side.

These are the steps needed for running the example:

__1º:__ Power on Raspberry Pi (Raspbian) and load __rpi_receiver__ folder into it.

__2º:__ Upload and run __receiver__ project folder onto land Lopy 4.

__3º:__ Upload __sender__ project folder into buoy's Lopy 4.

__4º:__ Run Python code contained in __rpi_receiver__ folder code, on Raspberry Pi. A Wi-Fi connection must be done manually for the first time to the receiver's network.

__5º:__ Run __sender__ project on buoy's Lopy4.

Finally after waiting several seconds, received data will begin to be written inside the __rpi_receiver__ folder under specific folders by their MACs.

The received content is saved in folders under the project folder, named by source MAC address.

## Caveats

- At this moment, due to the lack of datalogger connection, messages are being mocked up.
