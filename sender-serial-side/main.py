from CampbellScientificCR1000XWebRequest import CampbellScientificCR1000XWebRequest
from UARTInterface import UARTInterface


datalogger_web_request = CampbellScientificCR1000XWebRequest(host='192.168.4.20')

uart_interface = UARTInterface()
uart_interface.add_listener(datalogger_web_request)
uart_interface.listen()
