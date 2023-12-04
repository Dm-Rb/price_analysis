from threading import Thread
from auto1_parser import Auto1By
from avtoostrov_parser import AutoostrovBy
from zapby_parser import ZapBy
from remzona_db import DataBase
from shared_data_pool import DataPool


remzona_db = DataBase()  # init


class ThreadingManager:

    remzona_db = remzona_db

    # @classmethod
    # def create_remzona_db(cls):  # init
    #     cls.remzona_db = DataBase()

    def __init__(self, article, brand, supplier=None):
        self.prices_pool = []
        self.purchase_price = None
        remzona = Thread(target=self.remzona_db.main_get_price, args=(article, brand, supplier,))
        # auto1 = Thread(target=Auto1By.main, args=(article, brand,))
        # autoostrov = Thread(target=AutoostrovBy.main, args=(article, brand,))
        zap = Thread(target=ZapBy.main, args=(article, brand))

        remzona.start()
        # auto1.start()
        # autoostrov.start()
        zap.start()

        remzona.join()
        # auto1.join()
        # autoostrov.join()
        zap.join()

        self.prices_pool = DataPool.prices_pool.copy()
        DataPool.clear_dp()
        self.purchase_price = self.remzona_db.get_purchase_price()





