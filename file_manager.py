from configparser import ConfigParser
import os
import csv
import json
from datetime import datetime

class File:

    filename = None
    file_extension = None
    delimiter = ';'
    main_file_data = None

    @classmethod
    def __init__(cls):
        config = cls.__read_file_config()
        cls.filename, cls.file_extension = os.path.splitext(config['path'])
        cls.delimiter = config['delimiter']
        cls.main_file_data = cls.read_main_file()

    @classmethod
    def __read_file_config(cls, filename='config.ini', section='file') -> dict:
        # create parser and read ini configuration file
        parser = ConfigParser()
        parser.read(filename, encoding='utf-8')

        # get section, default to mysql
        db_config = {}
        if parser.has_section(section):
            items = parser.items(section)
            for item in items:
                db_config[item[0]] = item[1]
        else:
            raise Exception('{0} not found in the {1} file'.format(section, filename))

        return db_config

    @classmethod
    def read_main_file(cls):
        with open(cls.filename + cls.file_extension, 'r', encoding='utf-8') as r_file:
            file_reader = csv.DictReader(r_file, delimiter=cls.delimiter)
            file_data = list(file_reader)
            # cls.__create_empty_result_file(file_data[0])
            return file_data

    @classmethod
    def write_result_to_file(cls, result):
        try:
            file_path = cls.filename + "_result" + cls.file_extension
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(
                    f, fieldnames=result[0].keys(), quoting=csv.QUOTE_NONNUMERIC, delimiter=';')
                writer.writeheader()
                for row in result:
                    writer.writerow(row)
        except Exception as _ex:
            print(_ex)


class ExceptionsLogs(File):

    @classmethod
    def write_log(cls, *args):
        log_path = cls.filename + '.json'
        args = list(args).append(datetime.now())
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8', newline='') as f:
                data = json.load(f)
            data.append(args)
            with open(log_path, 'w', encoding='utf-8', newline='') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            with open(log_path, 'w', encoding='utf-8', newline='') as f:
                json.dump([args], f, ensure_ascii=False, indent=2)









