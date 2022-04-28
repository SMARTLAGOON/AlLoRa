'''
This class eases the use of a File divided in chunks
'''
import gc
import math

gc.enable()

class File:


    def __init__(self, name: str, content:bytes, chunk_size: int):
        self.__name = name
        self.__content = content
        self.__chunk_size = chunk_size
        self.__length = len(content)
        #self.__chunks = []

        self.chunk_counter = math.ceil(self.__length/self.__chunk_size)     #0

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
        return self.chunk_counter   #len(self.__chunks)


    def get_chunk(self, position: int):
        #print(self.__content)
        if self.last_chunk_sent is not None:
            if not self.check_retransmission(position):
                self.__content = self.__content[self.__chunk_size:]   # Se borra la data que ya se envió
                gc.collect()
        else:
            self.last_chunk_sent = position
        return self.__content[:self.__chunk_size]  #self.__chunks[position]


    def __chunkify(self, content):
        #chunk_counter = 0
        while content:
            self.__chunks.append(content[:self.__chunk_size])
            content = content[self.__chunk_size:]
            gc.collect()
            self.chunk_counter += 1
        """
        for i in range(0, self.__length, self.__chunk_size):
            if i == self.__length:
                break
            self.__chunks[chunk_counter] = content[i:(i + self.__chunk_size)]
            chunk_counter += 1
        self.chunk_counter = chunk_counter
        """


    ## For testing:
    def check_retransmission(self, requested_chunk):
        retransmission = False
        if requested_chunk == self.last_chunk_sent:
            self.retransmission += 1
            retransmission = True
        self.last_chunk_sent = requested_chunk
        return retransmission
