from configparser import ConfigParser
import os
import csv


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
            cls.__create_empty_result_file(file_data[0])
            return file_data

    @classmethod
    def __create_empty_result_file(cls, row):
        with open(cls.filename + "_result" + cls.file_extension, 'w', encoding='utf-8', newline='') as f:
            file_writer = csv.writer(f, delimiter=cls.delimiter, lineterminator="\r")
            row = list(row.keys()) + ['Remzona, розница', 'Auto1, розница', 'AutoOstrov, розница', 'Zap, розница']
            row += ['Remzona, наценка %', 'Auto1, наценка %', 'AutoOstrov, наценка %', 'Zap, наценка %']
            file_writer.writerow(row)
