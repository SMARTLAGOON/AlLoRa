from machine import UART
import _thread
import utime

class UARTParallelWritingException(Exception):

    def __init__(self, *args):
        super().__init__(args)


    def __str__(self):
        return "Only one serial writing operation can be carried out at the same time"


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
        self.__WRITING = False
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
                                break
                        except Exception as e:
                            pass
                    except Exception as e:
                        pass
                    utime.sleep(0.01)

            #FIXME Control exception
            command = command.decode('utf-8')[:-len("<<<END>>>")]
            # Parallel serial writing cannot be done by many threads at the same time, so, it can handle several listeners just if only one of them requires uart at the same time.
            for listener in self.__listeners:
                _thread.start_new_thread(listener.do_action, (command, self))


    def write(self, message: str):
        # This works since Processing does not exists in these devices.
        # Threads can be aware of changes immediately since they share cache.
        # To make this works with Processes, a proper lock may be required.
        if self.__WRITING == False:
            self.__WRITING = True
            print("write")
            length = len(message)
            to_send = ""
            self.__uart.write("<<<BEGIN>>>")
            #print("<<<BEGIN>>")
            for i in range(0, length, 256):
                if length - i < 256:
                    to_send = message[i:]
                else:
                    to_send = message[i:i+256]
                #print(to_send)
                self.__uart.write(to_send)
                utime.sleep(0.05)
            self.__uart.write("<<<END>>>")
            #print("<<<END>>>")
            print("write finished")
            self.__WRITING = False
        else:
            raise UARTParallelWritingException()
