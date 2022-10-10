from machine import UART
uart = UART(1, 115200)

print("OK")
while True:
	uart.write("Test = HOLA\n")
