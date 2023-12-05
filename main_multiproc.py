from threading_pars_manager import ThreadingManager
from file_manager import File
import time
import multiprocessing as mp


def update_row(row_table, result_list):
    # получить список цен из многопоточного менеджера парсеров
    obj = ThreadingManager(row_table['Каталожный номер'], row_table['Бренд'], row_table['Поставщик'])
    row_table['Закупочная цена'] = obj.purchase_price
    # добавить в цены с модифицироваными ключами в row_table
    for item in obj.prices_pool:
        key, value = list(item.items())[0]
        row_table.update({key + ' Розница': value})

    # добавить в разину закупочной цены с ключами в row_table
    for item in obj.prices_pool:
        key, value = list(item.items())[0]
        # value = round((float(value) - float(row_table['Цена'])) * 100 / float(row_table['Цена']), 1) if value else None

        if row_table['Закупочная цена']:
            value = round((float(value) - float(obj.purchase_price)) * 100 / float(obj.purchase_price), 1) if value else None

            row_table.update({key + ' Наценка %': value})

    # дозапись словаря в конец файла
    result_list.append(row_table)
    del obj


def generate_processes(*args):
    processes_list = [mp.Process(target=update_row, args=(i[0], i[1], )) for i in args]
    [process.start() for process in processes_list]
    [process.join() for process in processes_list]



if __name__ == "__main__":
    manager = mp.Manager()
    result_list = manager.list()
    # ThreadingManager.create_remzona_db()
    start_time = time.time()
    File()
    len_file_data = len(File.main_file_data)
    processes_quantity = 2
    for i in range(0, len_file_data, processes_quantity):
        print(i, len_file_data)
        if i == len_file_data - 1:
            generate_processes((File.main_file_data[i], result_list))
        else:
            generate_processes((File.main_file_data[i], result_list), (File.main_file_data[i + 1], result_list))

    File.write_result_to_file(result_list)
    end_time = time.time()
    execution_time = end_time - start_time
    print(execution_time)
    print("Done")