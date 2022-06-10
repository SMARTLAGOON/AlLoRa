import ujson
from lora_ctp.File import File
from DataSource import DataSource


class CampbellScientificCR1000XMockup(DataSource):


    def __init__(self, file_chunk_size: int, file_queue_size=25, sleep_between_readings=60, mockup_file_path= "./datalogger_output_mockup.json"):
        super().__init__(file_chunk_size, file_queue_size, sleep_between_readings)
        self.__mockup_data = self.__load_mockup(mockup_file_path)


    def __load_mockup(self, mockup_file_path: str) -> str:
        with open(mockup_file_path) as f:
            return ujson.load(f)


    def _read_datasource(self):
        print("read datasource")
        filename = self.__mockup_data['Output5min']['data'][0]['time']
        return File(name='{}.json'.format(filename), content=self.__mockup_data, chunk_size=super()._get_file_chunk_size())
