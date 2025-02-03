# AlLoRa Examples
---
By [Benjamín Arratia](https://www.barratia.com)

This folder contains examples of how to use AlLoRa in different devices and configurations. The examples are divided into four categories: Source, Requester, Gateway, and Adapters.

A basic AlLoRa setup consists of at least two devices: a Source and a Requester or a Gateway. The Source is the device that contains the data that we are interested in access at a long distance (e.g sensor data). 
The Requester is the device that requests the data from a single Source. The Gateway is a device that can request data from multiple Sources (a bigger version of the Requester).

The Adapter Nodes are devices that bridge the LoRa connection to another technology (WiFi, UART, etc). They are used to connect the LoRa module to a computer or a network.

A practical setup would be to have a LoRa-enabled ESP32 (LilyGo T3S3, Pycom LoPy4, etc) connected to a Sensor (DataSource), acting as a Source Node, another ESP32 like the first one acting as a Serial Adapter, connected to a Raspberry Pi acting as a Gateway. The Raspberry Pi will run the Gateway part of the code and send commands to the LoRa module through the Serial Adapter, which will send the AlLoRa commands to the Source Node. The data from the Sensor will end up in a folder with the mac address of the Source Node in the Raspberry Pi, after being successfully polled by the Gateway.

Let's try to run a simple example to understand how AlLoRa works.

## Example: Two T3S3 devices communicating:


### Requirements:

#### Hardware:
- Two [LilyGo T3S3 devices](https://lilygo.cc/products/t3s3-v1-0?variant=42586879688885). The examples were tested in Europe, so we used the SX1276 868MHz version. If you are in the US, you should use the 915MHz version.

#### Tools:

- Esptool installed on your machine, available in [this repository](https://github.com/espressif/esptool)
- Adafruit MicroPython tool: [Ampy](https://learn.adafruit.com/micropython-basics-load-files-and-run-code/install-ampy)

#### Firmware:

- Download micropython firmware available in this [folder](https://github.com/SMARTLAGOON/AlLoRa/tree/Dev/firmware/T3S3) and follow the instructions on how to flash it.
    

#### Software:

- For running examples, download the examples for the T3S3 [**Source**](https://github.com/SMARTLAGOON/AlLoRa/tree/main/examples/Sources/T3S3) and [**Requester**](https://github.com/SMARTLAGOON/AlLoRa/tree/main/examples/Requesters/T3S3).
- The rest is already in the [custom firmware](https://github.com/SMARTLAGOON/AlLoRa/tree/Dev/firmware).


### Running the example:

1.	Flash the custom firmware in both devices following the instructions in the [firmware folder](https://github.com/SMARTLAGOON/AlLoRa/tree/Dev/firmware/T3S3). 

2.	We will start configuring the Source Node first. Use [**ampy**](#installing-and-using-ampy) to “put” the files into the selected device. Upload the corresponding main and LoRa.json files like this:

    ```bash
    ampy --port /dev/tty.usbmodem1234561 put main.py 
    ampy --port /dev/tty.usbmodem1234561 put LoRa.json #Configuration file for AlLoRa
    ```
3. In order to run the example, you need to register the mac address of the Source Node in the Requester. You can find the mac address of the Source Node when it boots up. It will be printed in the console. Use [**REPL**](#repl) to interact with MicroPython directly on the board. In a mac computer you can use:

    ```bash
    screen /dev/tty.usbmodem1234561 115200
    ```

4. Once you access the REPL, you may need to reset the device to see the mac address. You can do this by pressing **Ctrl + D**. The mac address will be printed in the console. Copy it and paste it in the Requester's main.py file in line 17 of the provided example (node_mac_address = "XXXXXXXX"). 
5. Use ampy to upload the Requester's main.py and LoRa.json files to the Requester device.
6. With both devices configured, power them up and open two different terminals. Use the following commands to access the REPL of each device, replacing the port with the one corresponding to your device:

    ```bash
    screen /dev/tty.usbmodem1234561 115200
    ```
7. For a clean start, reset both devices by pressing **Ctrl + D** in the REPL.
8. The devices should start communicating and executing the example code, where the Source Node generates increasingly bigger files and the Requester polls it and saves the files in the Requester's memory. You can check the files in the Requester's memory using ampy or the REPL.



---
#### Installing and Using ampy
<details>
<summary>You can interact with the file system of the board using Adafruit’s ampy tool.</summary>

First, ensure it is installed:
```bash
pip3 install adafruit-ampy
```
Then, list the files on the board:
```bash
ampy --port /dev/tty.usbmodem1234561 ls
```
Retrieve a file from the board:
```bash
ampy --port /dev/tty.usbmodem1234561 get boot.py > boot.py
```
This command downloads boot.py from the board and saves it to your current directory.

More info about how ampy works here: [MicroPython Basics: Load Files & Run Code](https://learn.adafruit.com/micropython-basics-load-files-and-run-code/file-operations)
</details>

---
#### Accessing the REPL
<details>
  <summary>Access the REPL (Read-Eval-Print Loop) to interact with MicroPython directly on the board.</summary>

#### For macOS:

Using screen:
```bash
screen /dev/cu.usbmodem1234561 115200
```
To exit screen, press Ctrl-A followed by Ctrl-\.

### For Linux:

Using picocom (or similar):
```bash
picocom /dev/ttyUSB0 -b 115200
```
Make sure to replace /dev/ttyUSB0 with the actual port number found earlier. To exit picocom, press Ctrl-A followed by Ctrl-X.

Use Ctrl-D to soft reboot the board and interact with Micropython

With screen/picocom running, you should see the MicroPython prompt >>>. You can now type in Python commands and interact with the MicroPython environment on your board.
</details>

