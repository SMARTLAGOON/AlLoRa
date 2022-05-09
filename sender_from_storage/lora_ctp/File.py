'''
This class eases the use of a File divided in chunks
'''
import gc
from  math import ceil
from time import time, sleep, ticks_ms

gc.enable()

class File():

    def __init__(self, name: str, content:bytes, chunk_size: int):
        self.__name = name
        self.__content = content #memoryview(content)
        self.__chunk_size = chunk_size
        self.__length = len(content)
        #self.__chunks = [content[i:i + 200] for i in range(0, self.__length, 200)]
        self.chunk_counter = ceil(self.__length/self.__chunk_size)

        self.sent = False
        self.metadata_sent = False

        # For testing
        self.retransmission = 0
        self.last_chunk_sent = None

        self.first_sent = None
        self.last_sent = None

        #self.__chunkify(content)

    def get_name(self):
        return self.__name


    def get_content(self):
        return self.__content

    #Block length not characters
    def get_length(self):
        return self.chunk_counter   #len(self.__chunks)\

    def sent_ok(self):
        self.report_SST(False)
        self.sent = True

    def get_chunk(self, position: int):
        if self.last_chunk_sent:
            self.check_retransmission(position)
            #if not self.check_retransmission(position):
                #self.__content = self.__content[self.__chunk_size:]   # Se borra la data que ya se envió
                #gc.collect()
        self.last_chunk_sent = position
        return  (bytes(self.__content[position*self.__chunk_size : position*self.__chunk_size + self.__chunk_size])).decode()
        #self.last_chunk_sent = position
        #return (bytes(self.__chunks[position])).decode()
        #return self.__content[position*self.__chunk_size : position*self.__chunk_size + self.__chunk_size]
        #return (bytes(self.__content[position*chunk_size : (position + 1)*chunk_size])).decode()


    ## For testing:
    def check_retransmission(self, requested_chunk):
        retransmission = False
        if requested_chunk == self.last_chunk_sent:
            self.retransmission += 1
            retransmission = True
        return retransmission

    def report_SST(self, t0_tf):
        file_name = self.get_name()
    	t = time()

    	test_log = open('log.txt', "ab")
    	if t0_tf:
    		self.first_sent = t
    	else:
    		if self.first_sent is not None:
    			self.last_sent = t
    			txt = "{};t0;{};tf;{};SST;{};Retransmission;{}\n".format(self.get_name(), self.first_sent, t, t - self.first_sent, self.retransmission)
    			test_log.write(txt)
    			#if DEBUG == True:
    			print(txt)
    	test_log.close()
