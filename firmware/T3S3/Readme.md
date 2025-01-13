
# Flashing Micropython in LILYGO T3S3

### 1. Activate Boot Mode on the LILYGO T3S3

Before flashing, you need to activate the "boot mode":

- Hold down the "BOOT" button on the LILYGO T3S3 board.
- While holding the "BOOT" button, plug the board into your computer.
- Release the "BOOT" button once the board is connected.

### 2. Identify the Device Port

Locate the serial port of the connected board:

#### For macOS:

```bash
ls /dev/tty.*
```

For Linux:
```bash
ls /dev/ttyUSB*
```

### 3. Erase the Flash Memory

Erase the existing flash memory on the device:
```bash
esptool.py --chip esp32s3 --port /dev/cu.usbmodem101 erase_flash
```
Replace /dev/cu.usbmodem101 with the actual port identified earlier.

### 4. Flash the Firmware

Flash the new firmware onto the LILYGO T3S3 board:
```bash
esptool.py --chip esp32s3 --port /dev/cu.usbmodem101 write_flash -z 0x0 build-ESP32_GENERIC_S3/firmware.bin
```
Again, replace /dev/cu.usbmodem101 with your actual port.

### 5. Interact with the Board

After flashing, reset the board. This may cause the serial port to change, so you’ll need to identify the board’s port again.

Identify Board’s port

For macOS:
```bash
ls /dev/tty.*
```
For Linux:
```bash
ls /dev/ttyUSB*
```
Note the port number as you will need it for the following steps.
