from machine import UART
import _thread
import utime

class UARTInterfaceListener:


    def do_action(self, command: str):
        pass


class UARTInterface:


    __INSTANCE = None


    def __new__(klass, *args, **kwargs):
        if klass.__INSTANCE is None:
            klass.__INSTANCE = super().__new__(klass)
        return klass.__INSTANCE


    def __init__(self):
        self.__STOP_THREAD = False
        self.__uart = UART(1, 115000)
        self.__uart.init(115000, bits=8, parity=None, stop=1, pins=('P3', 'P4'))
        self.__listeners = list()


    def add_listener(self, listener: UARTInterfaceListener):
        self.__listeners.append(listener)


    def listen(self):
        # Wait for content
        while self.__STOP_THREAD is False:
            while (self.__uart.any() <= 0):
                utime.sleep(0.1)

            command = b""
            while True:
                    try:
                        raw = self.__uart.read(256)
                        command += raw
                        try:
                            if b"<<<END>>>" in raw:
                                print("exit raw")
                                break
                        except Exception as e:
                            pass

                    except Exception as e:
                        pass
                    utime.sleep(0.01)

            command = command.decode('utf-8')[:-len("<<<END>>>")]
            print("COMMAND", command)
            for listener in self.__listeners:
                _thread.start_new_thread(listener.do_action, (command, self))


    def write(self, message: str):
        print("write")
        length = len(message)
        to_send = ""
        for i in range(0, length, 256):
            if length - i < 256:
                to_send = message[i:-1]
            else:
                to_send = message[i:i+256]
            #print(to_send)
            self.__uart.write(to_send)
            utime.sleep(0.1)
        self.__uart.write("<<<END>>>")
