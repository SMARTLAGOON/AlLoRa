import _thread
import utime
import os
import ujson
from lora_ctp.File import File


class DataSource:


    def __init__(self, file_chunk_size: int, file_queue_size=25, sleep_between_readings=60):

        self.__STOP_THREAD = False

        self.__file_queue = []
        self.__file_queue_size = file_queue_size
        self.__file_chunk_size = file_chunk_size

        self.__get_next_file_called = False
        self.__SECONDS_BETWEEN_READINGS = sleep_between_readings

        self.__backup_file = None


    def _get_file_chunk_size(self):
        return self.__file_chunk_size


    def __add_to_queue(self, file: File):
        if len(self.__file_queue) >= self.__file_queue_size:
            self.__file_queue.pop(0)
        repeated = False
        for f in self.__file_queue:
            if f.get_name() == file.get_name():
                repeated = True
                break
        if repeated is False:
            self.__file_queue.append(file)


    def __read(self):
        while self.__STOP_THREAD is False:
            try:
                file = self._read_datasource()
                if file is not None:
                    self.__add_to_queue(file=file)
                else:
                    print("skipped file, it is None")
                utime.sleep(self.__SECONDS_BETWEEN_READINGS)
            except KeyboardInterrupt as e:
                self.stop()
        print(self.__STOP_THREAD)


    def _read_datasource(self) -> File:
        pass


    def _prepare(self):
        pass


    def start(self):
        self._prepare()
        _thread.start_new_thread(self.__read, ())


    def stop(self):
        self.__STOP_THREAD = True
        print(self.__STOP_THREAD)


    '''
    Everytime this function is called, it assumes the file is already consumed, so a deleting is performed.
    '''
    def get_next_file(self):
        try:
            backup_file = self.__file_queue.pop(0)
            self.__backup(file=backup_file)
            return backup_file
        except IndexError as e:
            return None


    def __backup(self, file: File):
        try:
            os.remove("./filename-backup.txt")
            os.remove("./content-backup.json")
        except OSError:
            pass

        with open("./filename-backup.txt", "w") as f:
            f.write(file.get_name())

        with open("./content-backup.json", "w") as f:
            ujson.dump(file.get_content(), f)


    def restore_from_backup(self):
        try:
            filename = ""
            with open("./filename-backup.txt", "r") as f:
                filename = f.read()

            content = None
            with open("./content-backup.json", "r") as f:
                content = ujson.load(f)

            rescued_file = File(name='{}'.format(filename), content=content, chunk_size=self.__file_chunk_size)
            self.__add_to_queue(file=rescued_file)
        except OSError as e:
            print("The backup could not be restored", e)
