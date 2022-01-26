'''
This class eases the use of a File divided in chunks
'''
class File:


    def __init__(self, name: str, content:bytes, chunk_size: int):
        self.__name = name
        self.__content = content
        self.__chunk_size = chunk_size
        self.__length = len(content)
        self.__chunks = dict()

        self.__chunkify()


    def get_name(self):
        return self.__name


    def get_content(self):
        return self.__content


    #Block length not characters
    def get_length(self):
        return len(self.__chunks)


    def get_chunk(self, position: int):
        return self.__chunks[position]


    def __chunkify(self):
        chunk_counter = 0
        for i in range(0, self.__length, self.__chunk_size):
            if i == self.__length:
                break
            self.__chunks[chunk_counter] = self.__content[i:(i + self.__chunk_size)]
            chunk_counter += 1
