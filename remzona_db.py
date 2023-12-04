from configparser import ConfigParser
from mysql.connector import MySQLConnection
from slugify import slugify
from shared_data_pool import DataPool


class DataBase(DataPool):

    @staticmethod
    def __read_db_config(filename='config.ini', section='mysql') -> dict:
        # create parser and read ini configuration file
        parser = ConfigParser()
        parser.read(filename)

        # get section, default to mysql
        db_config = {}
        if parser.has_section(section):
            items = parser.items(section)
            for item in items:
                db_config[item[0]] = item[1]
        else:
            raise Exception('{0} not found in the {1} file'.format(section, filename))

        return db_config

    def __init__(self):
        dbconfig = self.__read_db_config()
        self.connection = MySQLConnection(**dbconfig)
        self.suppliers = self.__get_suppliers()
        self.markup_exts = self.__get_markup_exts()
        # --
        self.supplier_articles = None
        self.purchase_price = None

    def __get_suppliers(self):
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""
                    SELECT * FROM `catalog_suppliers`
                    ;
                """
            )
            response = cursor.fetchall()
            if response:
                return response

    def __get_markup_exts(self):
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""
                    SELECT * FROM catalog_markup_exts
                    WHERE ext_mark_id = '2';
                    """
            )
            response = cursor.fetchall()
            if response:
                markups_without_brands_groups = list(filter(lambda i: (not i[1]) and (not i[2]), response))
                markups_without_brands_groups.sort(key=lambda x: x[3])
                return markups_without_brands_groups

    def __get_supplier_articles(self, article, brand, supplier):
        article = slugify(article)
        article = article.replace('-', '')
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""
                    SELECT * FROM `catalog_supplier_articles`
                    JOIN catalog_supplier_brands ON sbr_id = sar_sbr_id
                    JOIN catalog_suppliers ON sup_id = sbr_sup_id
                    JOIN catalog_supplier_prices ON pri_sar_id = sar_id
                    WHERE `sar_code` LIKE '{article}'
                    """
            )
            response = cursor.fetchall()
            if response:
                self.supplier_articles = response
                self.__filter_supplier_articles(brand, supplier)

    def __filter_supplier_articles(self, brand, supplier):

        # filtering by supplier
        if supplier:
            self.supplier_articles = list(filter(lambda x: x[16].lower() == supplier.lower(), self.supplier_articles))

        # filtering by brand
        if '/' in brand or ' ' in brand or '':
            brand_split = brand.split('/')
        else:
            brand_split = [brand]
        brand_split = [slugify(i).replace('-', '') for i in brand_split]
        if self.supplier_articles:
            self.supplier_articles = list(
                filter(lambda x: any([i in x[9] for i in brand_split]), self.supplier_articles))
            # leave a row with minimal price
            self.supplier_articles = min(self.supplier_articles, key=lambda x: x[29])

    def __get_price_without_brands_groups(self):
        end_r = len(self.markup_exts) - 1
        index = 0
        for i in range(end_r):
            first = self.markup_exts[i][3]
            last = self.markup_exts[i + 1][3]

            if self.supplier_articles[29] >= first and self.supplier_articles[29] < last:
                index = i
                break
            if i == end_r - 1:
                index = i + 1

        percent = self.markup_exts[index][4]
        markup = (self.supplier_articles[29] / 100) * percent
        return round(self.supplier_articles[29] + markup, 1)

    def get_purchase_price(self):
        if self.purchase_price:
            purchase_price = self.purchase_price
            self.purchase_price = None
            return purchase_price
        else:
            return None


    def main_get_price(self, article, brand, supplier=None):
        try:

            self.__get_supplier_articles(article, brand, supplier)
            if self.supplier_articles:
                self.purchase_price = float(self.supplier_articles[29])
                price = self.__get_price_without_brands_groups()
                # return price
                DataPool.append_dp({"remzona": float(price)})
            else:
                # return None
                DataPool.append_dp({"remzona": None})

        except Exception as ex:
            print(ex)
            # return None
            DataPool.append_dp({"remzona": None})
