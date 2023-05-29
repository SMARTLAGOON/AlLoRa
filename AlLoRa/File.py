import gc
from  math import ceil
try:
    from utime import ticks_ms as time
    import uos as os
except:
    from time import time
    import os
gc.enable()

'''
Analogous class to Lopy's one but instead of making chunks, this one reassembles them
'''
class CTP_File:

    def __init__(self, name: str = None, content: bytearray = None, chunk_size: int = None, length: int = None, report=False):
        self.name = name
        if content:
            self.assembly_needed = False
            self.content = content
            self.length = len(content)
            self.chunk_size = chunk_size
            self.chunk_counter = ceil(self.length/self.chunk_size)

            self.retransmission = 0
            self.last_chunk_sent = None

            self.sent = False
            self.metadata_sent = False
            self.first_sent = None
            self.last_sent = None
        else:
            self.assembly_needed = True
            self.content = bytearray()  # should be and empty bytearray
            self.length = length # Length in chunks
            self.chunks = dict()
            self.missing_chunks = list()

        self.report = report

    def get_name(self):
        return self.name

    def get_content(self):
        if self.assembly_needed:
            self.assembly()
        return self.content

    # Receiver methods
    def get_missing_chunks(self) -> list:
        self.assembly()
        return self.missing_chunks

    def add_chunk(self, order: int, chunk: bytes):
        self.chunks[order] = chunk
        print("CHUNK ADDED: ", len(self.chunks), "->", order, "->", str(chunk))

    def assembly(self):
        self.content = bytearray()
        self.missing_chunks = list()
        for i in range(0, self.length):
            try:
                self.content += self.chunks[i]
            except KeyError as e:
                self.missing_chunks.append(i)

    # Check if the folder exists and create it if not, then save the file on it
    def save(self, path):
        try:
            os.mkdir(path)
        except Exception as e:
            pass
        with open("{}/{}".format(path, self.name), "wb") as f:
            f.write(self.get_content())

    # Sender methods
    def get_length(self):
        return self.chunk_counter

    def sent_ok(self):
        self.report_SST(False)
        self.sent = True

    def get_chunk(self, position: int):
        if self.last_chunk_sent:
            self.check_retransmission(position)
        self.last_chunk_sent = position
        return bytes(self.content[position*self.chunk_size : position*self.chunk_size + self.chunk_size])

    def check_retransmission(self, requested_chunk):
        if requested_chunk == self.last_chunk_sent:
            self.retransmission += 1
            return True
        return False

    def report_SST(self, t0_tf, report=False):
        t = time()/1000
        if t0_tf:
            self.first_sent = t
        elif self.first_sent is not None:
            self.last_sent = t
            txt = "{} -> size: {} (chunks:{}) ;t0: {}; tf {}; SST: {}; Retransmission: {}\n".format(self.get_name(), self.length, self.chunk_counter, self.first_sent, t, t - self.first_sent, self.retransmission)
            print(txt)
            if report and self.report:
                test_log = open('log.txt', "ab")
                test_log.write(txt)
                test_log.close()

if __name__ == "__main__":
    x = CTP_File(name = "Test", length = 100)
    print(x.get_name())
    y = CTP_File(name = "Test2", content = bytearray(b"1111111111111111111"), chunk_size = 2)
    print(y.get_name())
