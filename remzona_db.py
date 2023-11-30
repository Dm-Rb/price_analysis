from configparser import ConfigParser
from mysql.connector import MySQLConnection
from slugify import slugify
from shared_data_pool import DataPool


class DataBase(DataPool):

    @staticmethod
    def read_db_config(filename='config.ini', section='mysql') -> dict:
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

    @staticmethod
    def filter_values(value_1: str, value_2: str):

        items = [value_1, value_2]
        for i in (0, 1):
            items[i] = slugify(items[i])
            items[i] = items[i].replace('-', '')

        if items[0] in items[1] or items[1] in items[0]:
            return True
        else:
            return False

    def __init__(self):
        dbconfig = self.read_db_config()
        self.connection = MySQLConnection(**dbconfig)
        self.markups_without_brands_groups = None
        self.get_catalog_markup_exts()

        # attrs db
        self.filtered_catalog_articles_rows = []
        self.catalog_supplier_articles = []
        self.catalog_supplier_prices = []

    def get_catalog_markup_exts(self):
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""
                    SELECT * FROM catalog_markup_exts
                    WHERE ext_mark_id = '2';
                    """
            )
            response = cursor.fetchall()
            if response:
                self.markups_without_brands_groups = list(filter(lambda i: (not i[1]) and (not i[2]), response))
                self.markups_without_brands_groups.sort(key=lambda x: x[3])

    def catalog_articles_get_rows(self, article_name):
        article_name = slugify(article_name).replace('-', '')
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""
                    SELECT * FROM catalog_articles
                    WHERE art_code = '{article_name}';
                    """
            )
            response = cursor.fetchall()
            if response:
                return response

    def catalog_supplier_brands_get_rows(self,  art_brand_id):
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""
                    SELECT * FROM catalog_supplier_brands
                    WHERE sbr_brand_id = '{art_brand_id}';
                    """
            )
            response = cursor.fetchall()
            if response:
                return response

    def get_and_filter_articles_rows(self, article_name, brand_name):
        catalog_articles = self.catalog_articles_get_rows(article_name)
        if catalog_articles:
            for item in catalog_articles:
                brand_rows_list = self.catalog_supplier_brands_get_rows(item[1])
                if brand_rows_list:
                    if any([self.filter_values(brand_name, i[2]) for i in brand_rows_list]):
                        self.filtered_catalog_articles_rows.append(item)

    def catalog_supplier_articles_get_rows(self):
        for item in self.filtered_catalog_articles_rows:
            if item:
                with self.connection.cursor() as cursor:
                    cursor.execute(
                        f"""
                            SELECT * FROM catalog_supplier_articles
                            WHERE sar_art_id = '{item[0]}';
                            """
                    )
                    response = cursor.fetchall()
                    if response:
                        self.catalog_supplier_articles.extend(response)

    def catalog_supplier_prices_get_rows(self):
        for item in self.catalog_supplier_articles:
            if item:
                with self.connection.cursor() as cursor:
                    cursor.execute(
                        f"""
                            SELECT * FROM catalog_supplier_prices
                            WHERE pri_sar_id = '{item[0]}';
                            """
                    )
                    response = cursor.fetchall()
                    if response:
                        self.catalog_supplier_prices.extend(response)

    def get_min_suppliers_price(self):
        prices = [i[4] for i in self.catalog_supplier_prices]
        if prices:
            return min([i[4] for i in self.catalog_supplier_prices])

    def get_price_without_brands_groups(self, min_suppliers_price):
        end_r = len(self.markups_without_brands_groups) - 1
        index = 0
        for i in range(end_r):
            first = self.markups_without_brands_groups[i][3]
            last = self.markups_without_brands_groups[i + 1][3]
            if min_suppliers_price >= first and min_suppliers_price < last:
                index = i
                break
            if i == end_r - 1:
                index = i + 1

        percent = self.markups_without_brands_groups[index][4]
        markup = (min_suppliers_price / 100) * percent
        return round(min_suppliers_price + markup, 1)

    def main_get_price(self, article_name, brand_name):
        try:
            self.get_and_filter_articles_rows(article_name, brand_name)
            self.catalog_supplier_articles_get_rows()
            self.catalog_supplier_prices_get_rows()
            min_suppliers_price = self.get_min_suppliers_price()

            self.filtered_catalog_articles_rows.clear()
            self.catalog_supplier_articles.clear()
            self.catalog_supplier_prices.clear()
            if min_suppliers_price:
                price = self.get_price_without_brands_groups(min_suppliers_price)
                # return price
                DataPool.append_dp({"remzona": float(price)})

        except Exception as ex:
            print(ex)
            # return None
            DataPool.append_dp({"remzona": None})
