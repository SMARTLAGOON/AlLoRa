import gc
from math import ceil
try:
    from utime import ticks_ms as time
    import uos as os
except:
    from time import time
    import os
gc.enable()

class OnDemandFileWriter:
    def __init__(self, filename):
        self.file = open(filename, 'wb')

    def write(self, data):
        self.file.write(data)

    def close(self):
        self.file.close()

class CTP_File:

    def __init__(self, name: str = None, content: bytearray = None, chunk_size: int = None, length: int = None, report=False, path="Results"):
        self.name = name
        self.report = report
        if content:
            self.assembly_needed = False
            self.content = content
            self.length = len(content)
            self.chunk_size = chunk_size
            self.chunk_counter = ceil(self.length / self.chunk_size)

            self.retransmission = 0
            self.last_chunk_sent = None

            self.sent = False
            self.metadata_sent = False
            self.first_sent = None
            self.last_sent = None
        else:
            self.assembly_needed = True
            self.length = length
            self.chunk_counter = length
            self.path = path
            # Check if Temp folder exists
            try:
                os.mkdir(f"{self.path}/Temp")
            except:
                pass
            self.temp_file_path = f"{self.path}/Temp/{name}.tmp"
            self.file_writer = OnDemandFileWriter(self.temp_file_path)
            self.received_chunks = 0
            self.missing_chunks = list(range(length))

    def get_name(self):
        return self.name

    def get_content(self):
        if self.assembly_needed:
            with open(self.temp_file_path, "rb") as f:
                self.content = f.read()
            return self.content
        return self.content

    # Requester methods
    def get_missing_chunks(self) -> list:
        return self.missing_chunks

    def add_chunk(self, order: int, chunk: bytes):
        try:
            self.file_writer.write(chunk)
            self.received_chunks += 1
            if order in self.missing_chunks:
                self.missing_chunks.remove(order)
        except Exception as e:
            print("Error adding chunk: ", e)

    def finalize(self, path=None):
        self.file_writer.close()
        if not path:
            path = self.path
        print("Trying to save file: ", self.temp_file_path + " -> " + path + "/" + self.name)
        os.rename(self.temp_file_path, path + "/" + self.name)

    def save(self, path=None):
        if path:
            try:
                os.mkdir(path)
            except:
                pass
        self.finalize(path)

    # Source methods
    def get_length(self):
        return self.chunk_counter

    def sent_ok(self):
        self.report_SST(False)
        self.sent = True

    def get_chunk(self, position: int):
        if self.last_chunk_sent:
            self.check_retransmission(position)
        self.last_chunk_sent = position
        return bytes(self.content[position * self.chunk_size: position * self.chunk_size + self.chunk_size])

    def check_retransmission(self, requested_chunk):
        if requested_chunk == self.last_chunk_sent:
            self.retransmission += 1
            return True
        return False

    def report_SST(self, t0_tf, report=False):
        t = time() / 1000
        if t0_tf:
            self.first_sent = t
        elif self.first_sent is not None:
            self.last_sent = t
            txt = "{} -> size: {} (chunks:{}) ;t0: {}; tf {}; SST: {}; Retransmission: {}\n".format(
                self.get_name(), self.length, self.chunk_counter, self.first_sent, t, t - self.first_sent,
                self.retransmission)
            print(txt)
            if report and self.report:
                with open('log.txt', "ab") as test_log:
                    test_log.write(txt.encode())

if __name__ == "__main__":
    x = CTP_File(name="Test", length=100)
    print(x.get_name())
    y = CTP_File(name="Test2", content=bytearray(b"1111111111111111111"), chunk_size=2)
    print(y.get_name())