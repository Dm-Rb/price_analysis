from threading import Thread
from auto1_parser import Auto1By
from avtoostrov_parser import AutoostrovBy
from zapby_parser import ZapBy
from remzona_db import DataBase
from shared_data_pool import DataPool


remzona_db = DataBase()  # init


def threading_manager(article, brand, supplier=None):
    remzona = Thread(target=remzona_db.main_get_price, args=(article, brand, supplier,))
    auto1 = Thread(target=Auto1By.main, args=(article, brand,))
    autoostrov = Thread(target=AutoostrovBy.main, args=(article, brand,))
    zap = Thread(target=ZapBy.main, args=(article, brand))

    remzona.start()
    auto1.start()
    autoostrov.start()
    zap.start()

    remzona.join()
    auto1.join()
    autoostrov.join()
    zap.join()

    prices = DataPool.prices_pool.copy()
    DataPool.clear_dp()

    return prices
