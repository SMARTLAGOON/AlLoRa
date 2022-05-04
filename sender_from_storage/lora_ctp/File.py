'''
This class eases the use of a File divided in chunks
'''
import gc
import math
import time

gc.enable()

class File:

    def __init__(self, name: str, content:bytes, chunk_size: int):
        self.__name = name
        self.__content = content
        self.__chunk_size = chunk_size
        self.__length = len(content)
        #self.__chunks = []

        self.chunk_counter = math.ceil(self.__length/self.__chunk_size)     #0

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
        #print(self.__content)
        if self.last_chunk_sent is not None:
            self.check_retransmission(position)
            #if not self.check_retransmission(position):
                #self.__content = self.__content[self.__chunk_size:]   # Se borra la data que ya se envió
                #gc.collect()
        else:
            self.last_chunk_sent = position
        return self.__content[position*self.__chunk_size : position*self.__chunk_size + self.__chunk_size]

    ## For testing:
    def check_retransmission(self, requested_chunk):
        retransmission = False
        if requested_chunk == self.last_chunk_sent:
            self.retransmission += 1
            retransmission = True
        self.last_chunk_sent = requested_chunk
        return retransmission

    def report_SST(self, t0_tf):
        file_name = self.get_name()
    	t = time.time()

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
