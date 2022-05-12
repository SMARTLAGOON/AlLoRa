'''
This class eases the use of a File divided in chunks
'''
import gc
from  math import ceil

gc.enable()

class File:

    def __init__(self, name: str, content:bytes, chunk_size: int):
        self.__name = name
        self.__content = content
        self.__chunk_size = chunk_size
        self.__length = len(content)
        #self.__chunks = dict()
        self.__chunk_counter = ceil(self.__length/self.__chunk_size)
        #self.__chunkify()

        self.__retransmission = 0
        self.__last_chunk_sent = None

        self.sent = False
        self.metadata_sent = False
        self.first_sent = None
        self.last_sent = None


    def get_name(self):
        return self.__name


    def get_content(self):
        return self.__content


    #Block length not characters
    def get_length(self):
        return self.chunk_counter   #len(self.__chunks)

    def sent_ok(self):
        self.report_SST(False)
        self.sent = True

    def get_chunk(self, position: int):
        if self.__last_chunk_sent:
            self.__check_retransmission(position)
        self.__last_chunk_sent = position
        return  (bytes(self.__content[position*self.__chunk_size : position*self.__chunk_size + self.__chunk_size])).decode()

    def __check_retransmission(self, requested_chunk):
        if requested_chunk == self.__last_chunk_sent:
            self.__retransmission += 1
            return True
        return False

    def report_SST(self, t0_tf):
        file_name = self.get_name()
    	t = time()

    	test_log = open('log.txt', "ab")
    	if t0_tf:
    		self.first_sent = t
    	else:
    		if self.first_sent is not None:
    			self.last_sent = t
    			txt = "{};t0;{};tf;{};SST;{};Retransmission;{}\n".format(self.get_name(), self.first_sent, t, t - self.first_sent, self.__retransmission)
    			test_log.write(txt)
    			#if DEBUG:
    			print(txt)
    	test_log.close()
