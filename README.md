# m<sup>3</sup>****LoRaCTP:**** modular, mesh, multi-device ****LoRa Content Transfer Protocol****

The code in **[this repository](https://github.com/GRCDEV/m3LoraCTP)** contains a toolbox that allows transferring content over a LoRa channel. It’s based on the original [LoRaCTP](https://github.com/pmanzoni/loractp), adding a more modular design with mesh capabilities and larger packet sizes for faster transfers. 

~~Details of the protocol can be found in this paper: (soon)~~

## Readme on Notion!
> For a better experience, you can check our awesome **Notion** description of the code [here...](https://barratia.notion.site/mLoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b)


## Content
- [m<sup>3</sup>****LoRaCTP:**** modular, mesh, multi-device ****LoRa Content Transfer Protocol****](#msup3suploractp-modular-mesh-multi-device-lora-content-transfer-protocol)
  - [Readme on Notion!](#readme-on-notion)
  - [Content](#content)
- [Folders](#folders)
  - [**m<sup>3</sup>LoRaCTP**](#msup3suploractp)
  - [Examples](#examples)
- [**How does it work?**](#how-does-it-work)
  - [→ Communication logic](#-communication-logic)
  - [→ Packet Structure](#-packet-structure)
    - [Flag composition](#flag-composition)
  - [→ Mesh mode](#-mesh-mode)
  - [→ Debug Hops](#-debug-hops)
- [Running an example](#running-an-example)
  - [→ **SMARTLAGOON_Buoy: How to use it**](#-smartlagoon_buoy-how-to-use-it)
  - [Hardware Requirements](#hardware-requirements)
  - [Setup:](#setup)
    - [Lopy4 + Pygate (Sender) & Lopy4 + Pysense 2.0 X (Adapter)](#lopy4--pygate-sender--lopy4--pysense-20-x-adapter)
    - [Raspberry Pi 4 (Gateway)](#raspberry-pi-4-gateway)
  - [Running the code](#running-the-code)

# Folders

## **m<sup>3</sup>LoRaCTP**


- It contains all the code necessary to setup a communication network between devices, from a point-to-point using two LoPy4’s, to a mesh with a gateway and multiple edge-nodes.
    
    ## [Nodes](https://github.com/GRCDEV/m3LoraCTP/tree/main/mLoRaCTP/Nodes)
    
    - A node is the element in charge of managing the communication logic for the Content Transfer Protocol.
        
        ### [Base_Node.py](https://github.com/GRCDEV/m3LoraCTP/blob/main/mLoRaCTP/Nodes/Base_Node.py)
        
        It is the parent class from whom the other nodes inherits them base and common attributes and methods.
        
        It receives a boolean to indicate if the system is working on **mesh mode** or not and a **[Connector](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b).**
        
        The Base Node is not supposed to be instantiated, it acts like an abstract class for the other Nodes (MicroPython doesn't support abstract classes, so we used a Parent class instead...)
        
        The main methods in this class are send_request and send_response.
        
        ### [Sender_Node.py](https://github.com/GRCDEV/m3LoraCTP/blob/main/mLoRaCTP/Nodes/Sender_Node.py)
        
        It is a structure whose purpose, as its name implies, is to send one or more [Files](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) . It waits and listens for requests from a [Receiver](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) or [Gateway](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) Node and syncs with them to send blocks (we call them chunks) of bytes of a [File,](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b)  until it finishes and is ready to send another one.  
        
        ### Usage
        
        ### [Sender Node](https://github.com/SMARTLAGOON/BuoySoftware/blob/ModuLoRa/mLoRaCTP/Nodes/Sender_Node.py) usage:
        
        1. Instantiation:
            
            For the user, the Sender must be instantiated with the same parameters explained in [Base Node](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b), plus:
            
            - name: A nickname for the Node, it shouldn’t be too large, we recommend a maximum of 3 characters, for the testing we used one letter (Nodes “A”, “B”, “C”…)
            - chunk_size (optional): It is the size of the payload of actual content to be sent in each [Packet](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b). The maximum and default chunk_size is 235 for p2p mode and 233 for mesh mode, but if for some reason the user prefers to make it smaller, this is the parameter to change.
        2. Establish Connection: 
            
            The first thing to do with the Sender is to use the establish_connection method. It will wait until a message for itself arrives, in order to sync with the Receiver/Gateway Node.
            
        3. Set a File:
            
            Now, we can start using the Node to send [Files](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b). For this, we use the set_file method, that receives a previously instantiated object of the class [File](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) (more about it above…). Another way to set a file to sent is with the restore_file method, but this is only supposed to be used when the code had some type of interruption, and we need to continue sending a File “mid-chunk”.
            
        4. Send the File:
            
            After this, we call the send_file method, and it will manage the transfer of all the chunks  of the File to be sent.
            
        
        ### Example:
        
        ```python
        from mLoRaCTP.Nodes.Sender_Node import mLoRaCTP_Sender
        
        lora_node = mLoRaCTP_Sender(name = "A", connector = connector,
        					chunk_size = 235, mesh_mode = True, debug = False)
        
        lora_node.establish_connection()
        lora_node.set_file(file_to_send)
        lora_node.send_file()
        ```
        
        ### [Receiver_Node.py](https://github.com/GRCDEV/m3LoraCTP/blob/main/mLoRaCTP/Nodes/Receiver_Node.py)
        
        It is a structure whose purpose, as its name implies, is to receive [Files](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b). It asks information to a [Sender](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b)  and listens for the responses. In order to communicate with an specific Node, the Receiver must have the information of this endpoint, for this,  we use the [Digital_Endpoint](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) class, who contains the MAC Address of the endpoint and manages the states of the communication and generates the complete [File](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) when the receiver finishes collecting all the chunks.
        
        ### Usage
        
        ### [Receiver Node](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) usage:
        
        1. Instantiation:
            
            For the user, the Receiver must be instantiated with the same parameters explained in [Base Node](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b), plus:
            
            - debug_hops (optional):  If True, the Senders will override the message to be sent and register the message path (or hops between Nodes), more information about this [here](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b).
            - NEXT_ACTION_TIME_SLEEP (optional): Is the time (in seconds) between actions for the receiver in order to listen to the sender. The default is 0.1 seconds, but you can experiment with this number if you want.
        2. Listen to endpoint:
            
            Once instantiated, we can use the method listen_to_endpoint, who needs a [Digital_Endpoint](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) to operate and a listening_time. We can use a loop to ensure that the [File](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) to be received arrives completely, but we can also use this listening_time to avoid getting stuck for too long while waiting for it to arrive.
            
        
        ### Example:
        
        ```python
        from mLoRaCTP.Nodes.Receiver_Node import mLoRaCTP_Receiver
        
        lora_node = mLoRaCTP_Receiver(connector = connector, mesh_mode = True, debug = False)
        
        lora_node.listen_to_endpoint(digital_endpoint, 300)
        
        #We can access the file like this:
        ctp_file = digital_endpoint.get_current_file()
        content = ctp_file.get_content()
        ```
        
        ### [Gateway_Node.py](https://github.com/GRCDEV/m3LoraCTP/blob/main/mLoRaCTP/Nodes/Gateway_Node.py)
        
        It is a practically a [Receiver Node](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) (actually, it inherits from it) but it has the capability to manage multiple [Sender Nodes](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b), receiving a list of [Digital_Endpoints](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b)  to check.
        
        ### Usage
        
        ### [Gateway Node](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) usage:
        
        1. Instantiation:
            
            For the user, the Gateway must be instantiated with the same parameters explained in [Receiver Node](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) plus:
            
            - TIME_PER_ENDPOINT: Time in seconds to focus per Node to listen, the default is 10 seconds.
        2. Set list of [Digital_Endpoints](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b):
            
            Create the necessary [Digital_Endpoints](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) to listen, add them to a list and give it to the Node with the set_digital_endpoints method
            
        3. Check them:
            
            Finally, execute the check_digital_endpoints method in order to listen all the nodes, each at a time, for the time that you indicated. This function contains a While True loop, because it’s supposed to keep listening periodically to the Nodes, so be careful when using it!
            
        
        ### Example:
        
        ```python
        from mLoRaCTP.Nodes.Sender_Node import mLoRaCTP_Gateway
        
        lora_node = mLoRaCTP_Gateway(mesh_mode = True, debug_hops = False, connector = connector)
        
        lora_gateway.set_digital_endpoints(list_of_digital_endpoints)
        lora_gateway.check_digital_endpoints()    # Listening for ever...
        ```
        
    
    ## [Connectors](https://github.com/GRCDEV/m3LoraCTP/tree/main/mLoRaCTP/Connectors)
    
    - A connector is the element that gives and manages the access to LoRa to a Node. The main objective of the connector is to make mLoRaCTP available to as many type of devices as possible. Many devices have embedded LoRa capabilities, while others maybe not, so the connector is a class that acts as a bridge to LoRa.
        
        ### [Connector.py](https://github.com/GRCDEV/m3LoraCTP/blob/main/mLoRaCTP/Connectors/Connector.py)
        
        It is the parent class from whom the connectors inherits them base attributes and methods.
        
        It manages the methods to send and receive data using raw LoRa, gives access to the RSSI of the last received package and the MAC address of the device. It also contains the method send_and_wait_response, whose function is to send a packet (usually with a request) and wait for a predefined period of time (WAIT_MAX_TIMEOUT).
        
        ### [Embedded_LoRa_LoPy.py](https://github.com/GRCDEV/m3LoraCTP/blob/main/mLoRaCTP/Connectors/Embedded_LoRa_LoPy.py)
        
        This type of connector is very straightforward, it uses the native library for using LoRa from the LoPy4 (Only tested in LoPy4)
        
        ### [Wifi_connector.py](https://github.com/GRCDEV/m3LoraCTP/blob/main/mLoRaCTP/Connectors/Wifi_connector.py)
        
        Is the counterpart of the [mLoRaCTP-WiFi_adapter](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b),  developed to use in a Raspberry Pi, but also tested on a regular computer. 
        
        ### [RPI_Dragino_connector](https://github.com/GRCDEV/m3LoraCTP/tree/main/mLoRaCTP/Connectors/RPi_Dragino_connector)
        
        - This connector was developed to use in a Raspberry Pi connected to a Dragino LoRa/HPS HAT for RPi v1.4. It uses the SX127x library to manage the Raspberry Pi’s GPIOs in order to control the Dragino and send packages using a LoRa channel.
            
            More testing is required with this one…
            
            ### [Dragino_connector.py](https://github.com/GRCDEV/m3LoraCTP/blob/main/mLoRaCTP/Connectors/RPi_Dragino_connector/Dragino_connector.py)
            
    
    ## [Adapters](https://github.com/GRCDEV/m3LoraCTP/tree/main/mLoRaCTP/Adapters)
    
    - Sometimes another device is needed in order to bridge to LoRa, depending of the technology used for the connection. In this cases, the code for the adapters will be in this folder, for now we have a WiFi to LoRa adapter:
        
        ### [mLoRaCTP-WiFi_adapter](https://github.com/GRCDEV/m3LoraCTP/tree/main/mLoRaCTP/Adapters/mLoRaCTP-WiFi_adapter)
        
        It contains the code for a LoPy4. It activates a hotspot for the Node to be bridged to connect to and a “light version” of a mix of the code of a Node and a Connector.  
        
        It operates in this way:
        
        <aside>
        🍓 Raspberry Pi/Computer Node (Wifi Connector) **←Wi-Fi→** LoPy4 with mLoRaCTP-WiFi_adapter **←LoRa→** Node
        
        </aside>
        
    
    ### → [Datasource.py](https://github.com/GRCDEV/m3LoraCTP/blob/main/mLoRaCTP/DataSource.py)
    
    A Datasource is a handy class that can be use to manage the files to be send. It is supposed to be used to feed Files to send to a Sender Nodes.
    
    ### → [Digital_Endpoint.py](https://github.com/GRCDEV/m3LoraCTP/blob/main/mLoRaCTP/Digital_Endpoint.py)
    
    Contains the MAC Address of the endpoint to communicate with and manages the states of the communication. It also manages the generation of the complete [File](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) when the receiver finishes collecting all the chunks.
    
    It also manages the “state” or phase in which the transfer is. 
    
    ### → [mLoRaCTP_File.py](https://github.com/GRCDEV/m3LoraCTP/blob/main/mLoRaCTP/mLoRaCTP_File.py)
    
    It is the class who focus on the actual File to be sent or received. It can be used to obtain the chunks of the content to transfer to the Sender Nodes and also assembly all the blocks received to obtain the complete File in the Receiver/Gateway side.
    
    It can be instantiated with content (byte array) to be used by the Sender to transmit the content, or it can also be instantiated as a “container”, in order to receive the chunks and finally assemble it to obtain the whole content, in the Receiver side.
    
    ### → [mLoRaCTP_Packet.py](https://github.com/GRCDEV/m3LoraCTP/blob/main/mLoRaCTP/mLoRaCTP_Packet.py)
    
    This class structures the actual packet to be sent through LoRa. It manages the creation of the message to be sent and also is capable of load the data received by LoRa in order to check that the message was correctly received (with checksum). 
    
    It is composed by a header and the actual payload. 
    
    More details about the structure of the packages [here](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b).
    

## Examples

- Contain examples of implementation of the mLoRaCTP code.
    
    ## **[SMARTLAGOON_Buoy](https://github.com/GRCDEV/m3LoraCTP/tree/main/examples/SMARTLAGOON_Buoy)**
    
    The code that inspired this implementation. It uses a Raspberry Pi 4 as a [Gateway Node](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b), interfacing with LoRa using a LoPy4 with the [mLoRaCTP-WiFi_adapter](https://github.com/SMARTLAGOON/BuoySoftware/tree/ModuLoRa/mLoRaCTP/Adapters/mLoRaCTP-WiFi_adapter) code and receiving messages from multiple Buoys that send the data collected by data loggers using a LoPy4 set up as a [Sender Node](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b).
    
    A class Buoy is defined, that inherits from [Digital Endpoint](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) and adds some specific capabilities specific for this project. The [Gateway Node](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) receives a list of (Digital) Buoys to listen to. 
    
    Something similar was made in the LoPy4 that is in the actual Buoy. It has a Data logger class that inherits from Datasource in order to feed the [Sender Node](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) with the Files to sent.
    
    You can check how to test it here [below](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b)…
    

# **How does it work?**

![Untitled](readme_assets/m3LoRaCTP_figures/Untitled.png)

As we can see in the image above, the protocol is structured in a symmetrical way. At the left we have the Sender side, with a [Sender Node](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b)  that receives a [mLoRaCTP File](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b)  to be sent from a [Data Source](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b), and uses a [Connector](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) to access LoRa to send [mLoRaCTP Packets](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b). 

At the right we have the Receiver side, with a [Receiver Node](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) that receives a [Digital Endpoint](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b), that provides the Sender information, in order to listen to it to receive the [mLoRaCTP File](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b), it also uses a [Connector](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) to access LoRa to receive the [mLoRaCTP Packets](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b), that contains the chunks (blocks of bytes) of the content transmitted.

## → Communication logic

The system follow a logic of requests from the Receiver to the Sender. Depending of the state of the state of the [Digital Endpoint](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b), the Receiver will send requests to the specific Sender and wait a time for an answer or reply. . If the answer does not arrive or it arrives with corruptions, the Receiver Node will repeat the request until the message arrives correctly (with a timeout when necessary).

The [Digital Endpoints](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) operates with the following states or phases of the communication:

[<img style="float: right;" src="readme_assets/m3LoRaCTP_figures/Untitled%201.png" width="350"/>](Untitled%201.png)

1. **Establish connection**
    
    Every Digital Endpoint start in this state, is sends a simple packet with the command “ok” and waits until a “ok” from the sender is received, then, it continues to the next state. 
    
2. **Ask metadata**:
    
    This is the first step for receiving a [mLoRaCTP File](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b), it asks the Sender for the metadata of the content to be received and waits until a Packet arrives with the name and the number of chunks of the content. In this stage, the [Digital Endpoint](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) creates an empty [mLoRaCTP File](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) object that will act as a container for the incoming chunks. If successful, it continues to the next state.
    
3. **Ask for data**
    
    In this state, the Receiver will sequentially ask for the chunks necessary to obtain the whole content. When a chunk arrives, it will feed the [mLoRaCTP](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) object until it collected all. When the [mLoRaCTP File](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) is complete, it will be assembled and the content will be ready to access or saved.
    
4. **Final acknowledge**
    
    In order to maintain the synchronization between the Nodes, a final acknowledge will be sent, and the system will wait until the Sender replies with an “ok” command.

**More information about how the [commands work](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) in the Packet Structure section*

## → Packet Structure

The  [mLoRaCTP_Packet](https://github.com/SMARTLAGOON/BuoySoftware/blob/ModuLoRa/mLoRaCTP/mLoRaCTP_Packet.py) is the element that is sent and receive through LoRa. It is designed to maximize the amount of actual content (or chunk size) sent each time, but also to ensure the correct reception of the package by the Node that is supposed to receive it. 

For compatibility’s sake, It is designed to have a maximum of 255 Bytes, that is the maximum size of a LoRa message on a LoPy4.

The header size is variable depending on the enabled mode (mesh or point-2-point), but both have in common a header of 20 Bytes, the first 16 Bytes contain the first 8 characters of the MAC Address of the source and destination Nodes. 1 Byte is destined to the message’s command and flags (explained in more detail [below](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b)). Another 3 Bytes are destined to the Checksum of the content, it is used to check if the content has arrived correctly or if it has some type of corruption. 

Finally, if the system is working in [Mesh mode](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) (detailed below), an additional 2 Bytes are used to store a message ID. The ID is a random number between 0 and 65.535 (the range of values that can be represented in binary using 2 Bytes) and it is used to manage the retransmissions when in mesh mode and to avoid chunk duplication in the receiver.

<table>
<tr>
<th>Point-2-point Packet</th>
<th>Mesh Packet</th>
</tr>
<tr>
<td>
<pre>
<img 
  src="readme_assets/m3LoRaCTP_figures/Untitled%202.png"
  title = "hola"
  width="300"
  />
</pre>
</td>
<td>

<img 
  src="readme_assets/m3LoRaCTP_figures/Untitled%202.png"
  title = "hola"
  width="300"
  />

</td>
</tr>
</table>



With this, the point-2-point Packet has 235 Bytes maximum for its payload, while the mesh Packet has 233 available Bytes. It seems like a small difference, but with 255 Bytes maximum per Packet, every Byte counts when sending Kilobytes of data.

### Flag composition

The Flag Byte is structured as follows:

<img src="readme_assets/m3LoRaCTP_figures/Untitled%204.png" 
alt="Picture" 
width="500" 
style="display: block; margin: 0 auto" />



- **Command bits**:
    
    2 bits that combined represent one of four type of commands:
    
    - **00 → DATA:** The command activated when the payload contains a requested chunk.
    - **01 → OK:** The acknowledgement command, it is used to establish connection between nodes or notify of the correct reception of the final chunk of the content being received. It usually implies that the payload is empty.
    - **10 →  CHUNK:** This command is used by the Receiver/Gateway to ask for a chunk of the content being received. The chunk number is stored in the payload, so the Sender can know what block is being requested.
    - **11 → METADATA:** This command is used by the Receiver/Gateway to ask for the metadata of the file to be received. If this is the case, the payload of the request will be empty. It is also used by the Sender to answer the request of metadata. In this case the payload contains the name and size of the File to sent.
- **Retransmission bit**:
    
    Not being used for the moment
    
- **Mesh bit:**
    
    1 bit that indicates if the message is supposed to be forwarded or not (more about this in the [Mesh mode](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) segment).
    
- **Hop bit:**
    
    1 bit that is True if the message was forwarded at some point (more about this in the [Mesh mode](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) segment).
    
- **Debug hop bit**
    
    1 bit that indicates that the message in question is in “debug hop mode” (more about this in the [Debug hops](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) segment).
    

## → Mesh mode

If the communication protocol has the mesh mode activated, the communication will work exactly the same as described [before](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b), but in the case of a request don’t being answered by a Sender for a specific number of times (set by the user), the [Digital Endpoint](https://www.notion.so/m3LoRaCTP-ec6d1adaabcb44b39bb59d41bdf75b9b) will jump to “retransmission mode”. Activating the mesh bit in the Packet in order to tell the other Nodes in the system to retransmit the message if received, to extend the reach of the system and try to establish the communication with the missing Node.

If a Sender Node receives a Packet that is not for itself, it usually discards it and keep listening for request directed to it. But with the mesh bit activated, it will forward it to help reach the real destination. For this forwarding, the Node sleeps for a random time between 0.1 and 1 second before sending it. This reduces the possibility of collisions between Packets when multiple Nodes are active and in reach between them. Each time a Packet is forwarded, the Hop bit of it will be activated in order to announce that it actually went through other devices during its path. When the destination Node receives its message, it notices that the message arrived using the “retransmission mode” and creates a response Packet with the mesh bit activated, because it assumes that if it arrived like this, it is probably that the response will reach the Gateway jumping through the same path. In this case, the Node doesn’t sleep before sending the response, prioritizing always the sender Node being requested something.

If the response Packet arrives with the Hop bit off to the Gateway, it means that it didn't go through any other Node in order response to the request, indicating that the retransmission maybe are not needed. In this cases the Gateway will deactivate the “retransmission mode” of this specific Digital Endpoint.

In order to avoid duplication and over retransmission of messages that could collapse the system, each new Packet is assigned a random ID by the Node, and is saved in a fixed-size list that is checked wherever a new message with mesh bit activated arrives. The Nodes also have another fixed-size list that saves all the forwarded message’s IDs and that checks to avoid forwarding multiple times the same Packet.

## → Debug Hops

The debug hops is an option available to activate when instantiating a Receiver or Gateway Node, and is a useful tool to check the path of a Packet when using the Mesh mode. It overrides the messages and focus on register in the payload each time the Packet goes through a Node. This information can be later retrieved in the Receiver/Gateway Node’s device’s memory and can be used to make decisions about the distribution of the Nodes in the area to cover.

The output of this process generates a log_rssi.txt file that looks like this:

```
022-06-17_17:11:40: ID=24768 -> [['B', -112, 0.5], ['A', -107, 0], ['B', -106, 0.3], ['C', -88, 0.2], ['G', -100, 0]]
2022-06-17_17:11:50: ID=2065 -> [['C', -99, 0.4], ['B', -93, 0], ['C', -93, 0.2], ['G', -105, 0]]
2022-06-17_17:11:53: ID=63728 -> [['C', -100, 0.4], ['B', -95, 0], ['C', -95, 0.5], ['G', -103, 0]]
2022-06-17_17:11:54: ID=32508 -> [['B', -114, 0], ['C', -95, 0.4], ['G', -103, 0]]
2022-06-17_17:11:56: ID=10063 -> [['C', -99, 0.1], ['B', -95, 0], ['C', -94, 0.1], ['G', -103, 0]]
```

Where it shows the time of reception, the ID of the message and then a list of hops that the Packet did. Each hop saves the  name of the Node, the RSSI of the last package received with LoRa when registering the hop, and the random time that the Node had to wait before forwarding the message. As we can see, in some cases this random sleep is 0. This is not random, because those Nodes were the destination of the requests of the Gateway, and, as commented before, they have the priority.

# Running an example

## → **[SMARTLAGOON_Buoy](https://github.com/GRCDEV/m3LoraCTP/tree/main/examples/SMARTLAGOON_Buoy): How to use it**

## Hardware Requirements

- [Raspberry Pi 4](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/) → Gateway
- 2 [Lopy4](https://pycom.io/product/lopy4/) → Sender and Wifi Adapter
- [Pysense 2.0 X](https://pycom.io/product/pysense-2-0-x/)
- [Pygate 868](https://pycom.io/product/pygate/)
- [Power over Ehternet (PoE) Adapter](https://pycom.io/product/power-over-ethernet-adapter/)

## Setup:

Download the code from [BuoySoftware](https://github.com/SMARTLAGOON/BuoySoftware) or clone the repo.

### Lopy4 + Pygate (Sender) & Lopy4 + Pysense 2.0 X (Adapter)

- 1. Updating the expansion boards (Pysense 2.0 X and Pygate)
    1. Follow this:
        
        [Updating Expansion Board Firmware](https://docs.pycom.io/chapter/pytrackpysense/installation/firmware.html)
        
        - TL;DR ⚡️
            
            <aside>
            ⚠️ You should remove the LoPy4 from the board for this step, we are only working with the Pysense 2 and the Pygate
            
            </aside>
            
            1. Download this: 
                
                • **[Pysense 2 DFU](https://software.pycom.io/findupgrade?key=pysense2.dfu&type=all&redirect=true)**
                
                • **[Pygate](https://software.pycom.io/findupgrade?key=pygate.dfu&type=all&redirect=true)**
                
            2. Install dfu-util: 
                - MacOs
                    
                    ```bash
                    brew install dfu-util
                    ```
                    
                - Linux
                    
                    ```bash
                    sudo apt-get install dfu-util
                    ```
                    
                - Windows
                    
                    Harder, follow the [official explanation](https://docs.pycom.io/chapter/pytrackpysense/installation/firmware.html) or check-out this video:
                    
                    [https://www.youtube.com/watch?v=FkycTZvj-ss](https://www.youtube.com/watch?v=FkycTZvj-ss)
                    
            3. Use dfu-util to update each expansion board
                
                Write this in the terminal
                
                - MacOs and Linux
                    - Update Pysense 2:
                        
                        ```bash
                        sudo dfu-util -D pysense2_v16.dfu #This name will change with new versions, match it...
                        ```
                        
                    - Update Pygate:
                        
                        ```bash
                        sudo dfu-util -D pygate_v13_1049665.dfu #This name will change with new versions, match it...
                        ```
                        
                - Windows
                    - Update Pysense 2:
                        
                        ```bash
                        dfu-util-static.exe -D #This name will change with new versions, match it...
                        ```
                        
                    - Update Pygate:
                        
                        ```bash
                        dfu-util-static.exe -D #This name will change with new versions, match it...
                        ```
                        
                
                Connect the expansion board to your computer while pressing the DFU button (toggle to check where it is depending of the board...)
                
                - Pysense 2
                    
                    ![Untitled](readme_assets/Hardware_Setup/Untitled.png)
                    
                - Pygate
                    
                    ![Untitled](readme_assets/Hardware_Setup/Untitled%201.png)
                    
                
                Wait 1 second, release the DFU button and press enter in the terminal to run the code.
                
                As a result, you should expect something like this:
                
                ![Untitled](readme_assets/Hardware_Setup/Untitled%202.png)
                
            4. Check it with:
                
                ```bash
                lsusb
                ```
                
                You should expect something like this:
                
                ```bash
                Bus 000 Device 001: ID 04d8:f012 Microchip Technology Inc. Pysense  Serial: Py8d245e
                ```
                
- 2. Update the Lopy4’s
    1. Download the Pycom Firmware Tool from:
        
        [Updating Device Firmware](https://docs.pycom.io/updatefirmware/device/)
        
    2. Download this legacy firmware: [LoPy4-1.19.0.b4.tar.gz](https://software.pycom.io/downloads/LoPy4-1.19.0.b4.tar.gz)
        - (You can find it here)
            
            [Firmware Downgrade](https://docs.pycom.io/advance/downgrade/)
            
    3. Connect each LoPy4 to it’s respective Expansion Board (The LED side of the LoPy should be facing the USB port of the expansion board) ant then plug it on your computer
    4. Open Pycom Firmware Tool and press continue 2 times to get to the “Communication” section
    5. Select the port and the speed (for me 115200 worked ok), select the “Show Advanced Settings” checkbox and select “Flash from local file” and locate the firmware that we downloaded a few steps before (LoPy4-1.19.0.b4.tar.gz).
    6. Select the Erase flash file system and Force update LoRa region and press continue
    7. In the LoRa region selection select your country or region to establish your LoRa frequency.
    8. Press “Done” and it should start updating
    9. Repeat this step with the other LoPy4 with it’s respective expansion board...
- 3. Setting the environment
    
    [documentation](https://docs.pycom.io/gettingstarted/software/)
    
    We’ll need to upload the programs using PyMakr, a library that can be installed into [VS Code](https://code.visualstudio.com/) and [Atom](https://atom.io/) (I will refer to them as [IDE](https://en.wikipedia.org/wiki/Integrated_development_environment))
    
    <aside>
    ⚠️ I’m personally using an M1 Pro Macbook Pro and Atom with PyMakr and it’s working fine for me.
    
    </aside>
    
    - Here is the official Pycom guide to using Atom + PyMakr:
        
        [Atom](https://docs.pycom.io/gettingstarted/software/atom/)
        
    - If you want to use VS Code, here are the official Pycom instructions:
        
        [Visual Studio Code](https://docs.pycom.io/gettingstarted/software/vscode/)
        
    
    Once you have everything installed and working, you should be able to connect your LoPy4 + expansion board (Pygate  and Pysense 2.0 X for the sender and the receiver respectively) to your computer using an USB cable and PyMakr should recognise it. 
    
- 4. Uploading and running the code
    
    ### Sender:
    
    1.  Open the sender folder of the repo in your IDE
    2. Connect your LoPy4 + Pygate to your computer. PyMakr should recognise it and show you something like this:
        
        ![Untitled](readme_assets/Hardware_Setup/Untitled%203.png)
        
        - If it doesn’t do it automatically, you can open the “Connect Device” option and manually select your Port:
            
            ![Untitled](readme_assets/Hardware_Setup/Untitled%204.png)
            
    3. Press Ctrl+Alt/Opt + s or the “Upload Project to Device” button to upload the code to the LoPy4
        
        ![Untitled](readme_assets/Hardware_Setup/Untitled%205.png)
        
        With this, the code will boot automatically each time the LoPy4 is on. 
        
    4. If everything is ok, you should see something like this on the terminal: 
        
        ![Untitled](readme_assets/Hardware_Setup/Untitled%206.png)
        
        Register your LoPy4’s MAC Address (we will use it later...), in this example mine is: 70b3d5499973b469
        
    
    ### Adapter:
    
    <aside>
    ✌🏻 The process is exactly the same that for the [sender](https://www.notion.so/SMARTLAGOON-Buoy-Hardware-Setup-078125eb60f94dcdb6abdb86607a1fb2), but changing the project folder... (and [steps #4](https://www.notion.so/SMARTLAGOON-Buoy-Hardware-Setup-078125eb60f94dcdb6abdb86607a1fb2) and [#5](https://www.notion.so/SMARTLAGOON-Buoy-Hardware-Setup-078125eb60f94dcdb6abdb86607a1fb2))
    
    </aside>
    
    1.  Open the mLoRaCTP-WiFi_adapter folder of the repo in your IDE
    2. Connect your LoPy4 + PySense 2.0 X to your computer. PyMakr should recognise it and show you something like this:
        
        ![Untitled](readme_assets/Hardware_Setup/Untitled%203.png)
        
        - If it doesn’t do it automatically, you can open the “Connect Device” option and manually select your Port:
            
            ![Untitled](readme_assets/Hardware_Setup/Untitled%204.png)
            
    3. Press Ctrl+Alt/Opt + s or the “Upload Project to Device” button to upload the code to the LoPy4
        
        ![Untitled](readme_assets/Hardware_Setup/Untitled%205.png)
        
        With this, the code will boot automatically each time the LoPy4 is on. 
        
    4. If everything is ok, you should see something like this on the terminal: 
        
        ![Untitled](readme_assets/Hardware_Setup/Untitled%207.png)
        
    5. Open the boot file and check line number #9:
        
        ![Untitled](readme_assets/Hardware_Setup/Untitled%208.png)
        
         Those are the SSID and Password of the Lopy4's Wi-Fi hotspot, we will need this info in order to [connect the Raspberry Pi 4 to it late](https://www.notion.so/SMARTLAGOON-Buoy-Hardware-Setup-078125eb60f94dcdb6abdb86607a1fb2)
        

### Raspberry Pi 4 (Gateway)

1. Setup your Raspberry Pi 4 with [Raspberry Pi OS 32bit](https://www.raspberrypi.com/software/) and [install Python 3.8.](https://itheo.tech/install-python-38-on-a-raspberry-pi)
2. Download the rpi_gateway folder from [BuoySoftware](https://github.com/SMARTLAGOON/BuoySoftware)
3. Install Python3.8 dependencies using:
    
    ```bash
    sudo python3.8 pip install -r requirements.txt
    ```
    
4. Register your LoPy’s Mac Address into the ****buoy-list.json**** like this:
    
    ```json
    [
    {
        "name": "A",
        "lat": 37.6996,
        "lon": -0.7858,
        "alt":0,
        "mac_address": "70b3d5499a76ba3f",
        "uploading_endpoint": "https://heterolistic.ucam.edu/api/applications/607816fe4e830d00204224c0/userHardSensors/61fcf9dc3ea3c800203a9d35/data",
        "active": true
      }
    ]
    ```
    
    Make sure to put set the active flag to true!
    
5. Check and change the config.ini if needed:

```json
[receiver]
RECEIVER_MAC_ADDRESS = 70b3d549933c91d4
RECEIVER_API_HOST = 192.168.4.1
RECEIVER_API_PORT = 80
SOCKET_TIMEOUT = 10
PACKET_RETRY_SLEEP = 0.5
SOCKET_RECV_SIZE = 10000

[general]
SYNC_REMOTE = False
SYNC_REMOTE_FILE_SENDING_TIME_SLEEP = 5
SYNC_REMOTE_FILE_SENDING_MAX_RETRIES = 10
NEXT_ACTION_TIME_SLEEP = 0.1
SYNC_REMOTE_DIRECTORY_UPDATE_INTERVAL_SECONDS = 5
TIME_PER_BUOY = 10
MAX_RETRANSMISSIONS_BEFORE_MESH = 10
```

## Running the code

1. Power on everything ⚡️ (The LoPy4’s and the Raspberry Pi 4). Both LoPy4’s should start booting their code automatically if all the previous steps were successful.
2. Connect the RP4 to internet using its Ethernet Port (optional for uploading the received data to the cloud)
3. Open the Wi-Fi settings in the RP4 and connect to the receiver’s [Wi-Fi hotspot](https://www.notion.so/SMARTLAGOON-Buoy-Hardware-Setup-078125eb60f94dcdb6abdb86607a1fb2)
4. Go to the rpi_gateway folder in the Raspberry Pi 4 and open the terminal (we will use it soon...)
5. If not already done, open and edit the [buoy-list.json](https://github.com/SMARTLAGOON/BuoySoftware/blob/main/rpi_receiver/buoy-list.json), leave only one buoy and change the mac_address to the one that we found previously [here](https://www.notion.so/SMARTLAGOON-Buoy-Hardware-Setup-078125eb60f94dcdb6abdb86607a1fb2).
    
    You can change the name and other properties If you want to. 
    
    <aside>
    🛠 If you want to add other devices (other buoys), you should add them manually in this JSON file.
    
    </aside>
    
6. With everything ready, run the [main.py](https://github.com/SMARTLAGOON/BuoySoftware/blob/main/rpi_receiver/main.py) in the RP4 like this:
    
    ```bash
    python3.8 main.py
    ```
    
    If everything is ok, the RP4 should start receiving data from the Wifi adapter (and the adapter from the Sender) and create a folder with the MAC address of the Sender Node and register the received data inside.