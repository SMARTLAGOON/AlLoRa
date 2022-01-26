'''
Analogous class to Lopy's one but instead of making chunks, this one reassembles them
'''
class File:


    def __init__(self, name: str, length: int):
        self.__name = name
        self.__chunks = dict()
        self.__length = length
        self.__content = str()
        self.__missing_chunks = list()


    def get_name(self):
        return self.__name


    def get_content(self):
        self.__assembly()
        return self.__content


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