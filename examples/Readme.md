# Setting up AlLoRa  in LILYGO T3S3

By [Benjamín Arratia](https://www.notion.so/Benjam-n-Arratia-87712584b5584733ac66c90eab5e4e99?pvs=21)

---


### Requirements:
#### Tools:

- Esptool installed on your machine, available in [this repository](https://github.com/espressif/esptool)
- Adafruit MicroPython tool: [Ampy](https://learn.adafruit.com/micropython-basics-load-files-and-run-code/install-ampy)

#### Firmware:

- Download micropython firmware available in this [folder](https://github.com/SMARTLAGOON/AlLoRa/tree/Dev/firmware/T3S3) and follow the instructions on how to flash it.
    

#### Software:

- For running examples, download the examples for [**Source**](https://github.com/SMARTLAGOON/AlLoRa/tree/main/examples/Sources/T3S3) and [**Requester**](https://github.com/SMARTLAGOON/AlLoRa/tree/main/examples/Requesters/T3S3).
- The rest is already in the [custom firmware](https://github.com/SMARTLAGOON/AlLoRa/tree/Dev/firmware).


## Running AlLoRa in T3S3

 1.	Use [**ampy**](#installing-and-using-ampy) to “put” the files into the micropython device . Some are .py files like your main.py and others can be .mpy like PyLora_SX127x_extensions. (How to generate the .mpy files? )
 

```bash
ampy --port /dev/tty.usbmodem1234561 ls #To check the files
ampy --port /dev/tty.usbmodem1234561 put PyLora_SX127x_extensions
ampy --port /dev/tty.usbmodem1234561 put AlLoRa
```

2.	For each device put the corresponding main and LoRa.json file
```bash
ampy --port /dev/tty.usbmodem1234561 put main.py 
ampy --port /dev/tty.usbmodem1234561 put LoRa.json #Configuration file for AlLoRa
```

3.	Use [**REPL**](#repl) to interact with MicroPython directly on the board. In a mac computer you can use:

```bash
screen /dev/tty.usbmodem1234561 115200
```

To evaluate the execution of the code. Start by soft resetting the device with **Ctrl + D**.
The devices should start communicating and executing the example code

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

