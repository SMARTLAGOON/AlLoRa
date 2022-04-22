'''
This class eases the use of a File divided in chunks
'''
class File:


    def __init__(self, name: str, content:bytes, chunk_size: int):
        self.__name = name
        #self.__content = content
        self.__chunk_size = chunk_size
        self.__length = len(content)
        self.__chunks = dict()

        self.chunk_counter = 0

        # For testing
        self.retransmission = 0
        self.last_chunck_sent = None

        self.first_sent = None
        self.last_sent = None

        self.__chunkify(content)

    def get_name(self):
        return self.__name


    def get_content(self):
        return self.__content


    #Block length not characters
    def get_length(self):
        return len(self.__chunks)


    def get_chunk(self, position: int):
        self.check_retransmission(position)
        return self.__chunks[position]


    def __chunkify(self, content):
        chunk_counter = 0
        for i in range(0, self.__length, self.__chunk_size):
            if i == self.__length:
                break
            self.__chunks[chunk_counter] = content[i:(i + self.__chunk_size)]
            chunk_counter += 1
        self.chunk_counter = chunk_counter

    ## For testing
    def check_retransmission(self, requested_chunk):
        if requested_chunk == self.last_chunck_sent:
            self.retransmission += 1
        self.last_chunck_sent = requested_chunk
