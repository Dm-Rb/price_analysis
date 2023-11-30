from threading_pars_manager import threading_manager
from file_manager import File
import time
import csv


def update_row(row_table):
    # получить список цен из многопоточного менеджера парсеров
    prices = threading_manager(row_table['Каталожный номер'], row_table['Бренд'])

    # сгенерировать массив со значениями процента от закупочной стоимости
    markup_percent = []
    for item_pool in prices:
        key, value = list(item_pool.items())[0]
        markup_percent.append(
            {
                key: round((float(value) - float(row_table['Цена'])) * 100 / float(row_table['Цена']), 1) if value else None
            }
        )
    # добавить значения списка цен в row_table
    for item in prices:
        if item.get('remzona', False):
            row_table['Remzona, розница'] = item['remzona']
        elif item.get('auto1', False):
            row_table['Auto1, розница'] = item['auto1']
        elif item.get('avtoostrov', False):
            row_table['AutoOstrov, розница'] = item['avtoostrov']
        elif item.get('zap', False):
            row_table['Zap, розница'] = item['zap']

    # добавить значения процента от цен в row_table
    for item in markup_percent:
        if item.get('remzona', False):
            row_table['Remzona, наценка %'] = item['remzona']
        elif item.get('auto1', False):
            row_table['Auto1, наценка %'] = item['auto1']
        elif item.get('avtoostrov', False):
            row_table['AutoOstrov, наценка %'] = item['avtoostrov']
        elif item.get('zap', False):
            row_table['Zap, наценка %'] = item['zap']
    # дозапись словаря в конец файла
    write_row_to_file_in_end(row_table)
    # return row_table


def write_row_to_file_in_end(row_table):
    # Убрать нахуй и разобраться как создавать общий пул данных для разных процессов!
    try:
        path = 'Patron_30_11_result.csv'
        with open(path, 'a', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(
                f, fieldnames=row_table.keys(), quoting=csv.QUOTE_NONNUMERIC, delimiter=';')
            writer.writerow(row_table)
    except Exception as _ex:
        print(_ex)


if __name__ == "__main__":
    start_time = time.time()
    File()
    len_file_data = len(File.main_file_data)
    for i in range(0, len_file_data):
        print(f"row {str(i + 1)} / {str(len_file_data + 1)}")
        update_row(File.main_file_data[i])

    end_time = time.time()
    execution_time = end_time - start_time
    print(execution_time)
    print("Done")
