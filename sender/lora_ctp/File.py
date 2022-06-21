'''
This class eases the use of a File divided in chunks
'''
import gc
from  math import ceil
from time import time
gc.enable()

'''
Analogous class to Lopy's one but instead of making chunks, this one reassembles them
'''
class File:

    def __init__(self, name: str = None, content: bytearray = None, chunk_size: int = None, length: int = None):
        self.__name = name

        if content:
            self.assembly_needed = False
            self.__content = content
            self.__length = len(content)
            self.__chunk_size = chunk_size
            self.__chunk_counter = ceil(self.__length/self.__chunk_size)

            self.retransmission = 0
            self.__last_chunk_sent = None

            self.sent = False
            self.metadata_sent = False
            self.first_sent = None
            self.last_sent = None
        else:
            self.assembly_needed = True
            self.__content = str()  # should be and empty bytearray
            self.__length = length # Length in chunks
            self.__chunks = dict()
            self.__missing_chunks = list()

            #Timestamp is not saved along the rest of variables, so in case of network shutdown or something, the record will not respect the timeseries
            self.__timestamp = int(time() * 1000) #FIXME This is a temporal solution until the datalogger can put a timestamp


    def get_name(self):
        return self.__name

    def get_content(self):
        if self.assembly_needed:
            self.__assembly()
        return self.__content

    # Receiver methods

    def get_timestamp(self):
        return self.__timestamp

    def get_missing_chunks(self) -> list:
        self.__assembly()
        return self.__missing_chunks

    def add_chunk(self, order: int, chunk: bytes):
        self.__chunks[order] = chunk

    def __assembly(self):
        self.__content = str()
        self.__missing_chunks = list()
        for i in range(0, self.__length):
            try:
                self.__content += self.__chunks[i].decode('utf-8')
            except KeyError as e:
                self.__missing_chunks.append(i)

    # Sender methods
    def get_length(self):
        return self.__chunk_counter

    def sent_ok(self):
        self.report_SST(False)
        self.sent = True

    def get_chunk(self, position: int):
        if self.__last_chunk_sent:
            self.__check_retransmission(position)
        self.__last_chunk_sent = position
        return bytes(self.__content[position*self.__chunk_size : position*self.__chunk_size + self.__chunk_size]).decode()

    def __check_retransmission(self, requested_chunk):
        if requested_chunk == self.__last_chunk_sent:
            self.retransmission += 1
            return True
        return False

    def report_SST(self, t0_tf):
        file_name = self.get_name()
        t = time()
        if t0_tf:
            self.first_sent = t
        elif self.first_sent is not None:
            self.last_sent = t
            test_log = open('log.txt', "ab")
            txt = "{};t0;{};tf;{};SST;{};Retransmission;{}\n".format(self.get_name(), self.first_sent, t, t - self.first_sent, self.retransmission)
            test_log.write(txt)
            #if DEBUG:
            print(txt)
            test_log.close()


if __name__ == "__main__":
    x = File(name = "Test", length = 100)
    print(x.get_name())
    y = File(name = "Test2", content = bytearray(b"1111111111111111111"), chunk_size = 2)
    print(y.get_name())
