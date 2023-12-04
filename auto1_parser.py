import requests
from user_agent import user_agent
from bs4 import BeautifulSoup
from slugify import slugify
from brand_names_synonym import synonyms_dict
from shared_data_pool import DataPool
from file_manager import ExceptionsLogs


class Auto1By(DataPool):

    __session = requests.Session()
    __host = 'https://auto1.by'
    article = None
    brand = None

    @classmethod
    def __get_html(cls, url: str, host: bool = True, json: bool = False):
        response = cls.__session.get(url=cls.__host + url if host else url, headers=user_agent)
        if response.status_code == 200:
            if json:
                return response.json()
            else:
                return response.text

    @classmethod
    def find_articles(cls, article, brand_name):
        cls.article = article
        cls.brand = brand_name

        result_list = []
        tail_url = f'/search?pattern={cls.article.replace(" ", "+")}'
        html = cls.__get_html(url=tail_url)
        soup = BeautifulSoup(html, "html.parser")
        row_list = soup.find_all('div', class_='search-results-row')
        if row_list:
            for row in row_list:
                try:
                    a_list = row.find_all('a')
                    # Ожидается, что row  имеет 3 <a>, где [0]-article, [1]-brand, [2]-group
                    article_name = a_list[0].text
                    if cls.__filter_values(article_name, cls.article):
                        brand_item = a_list[1].text.replace('\t', '').replace('\n', '').strip()
                        if cls.__filter_values(brand_item, brand_name):
                            item = {
                                "brand": brand_item,
                                "article_name": article_name,
                                "article_detail_url": a_list[0]['href']
                                }
                            if item not in result_list:
                                result_list.append(item)
                except Exception as _ex:
                    print(_ex)
                    continue
        return result_list

    @staticmethod
    def __filter_values(value_1: str, value_2: str):

        synonyms_keys = synonyms_dict.keys()
        if value_1 in synonyms_keys:
            value_1 = synonyms_keys[value_1]
        if value_2 in synonyms_keys:
            value_2 = synonyms_keys[value_2]

        items = [value_1, value_2]
        for i in (0, 1):
            items[i] = slugify(items[i])
            items[i] = items[i].replace('-', '')

        if items[0] in items[1] or items[1] in items[0]:
            return True
        else:
            return False

    @classmethod
    def get_price_article_from_page(cls, article_detail_url):
        result_list = []
        html = cls.__get_html(url=article_detail_url)
        soup = BeautifulSoup(html, "html.parser")
        parent_div = soup.find('div', class_='details').find('tbody').find_all('tr')
        for tr in parent_div:
            td_list = tr.find_all('td')
            # Ожидается, что td_list  имеет 6 <td>, где [0]-поставщик, [1]-поставка, [2]-импорт, [3]-остаток, [4]-прайс, [5]-купить
            if len(td_list) == 6:
                span_list = [i.text.replace("\n", '').replace("\t", '').strip() for i in td_list[4].find_all('span')]
                if len(span_list) > 1:
                    result_list.append(min([i for i in span_list if i.replace(',', '').isdigit()]))
                else:
                    result_list.append(span_list[0])
        if result_list:
            min_price = str(min([float(i.replace(',', '.')) for i in result_list]))
            return min_price

    @classmethod
    def main(cls, article, brand_name):
        try:
            found_items = cls.find_articles(article, brand_name)
            if found_items:
                for i in range(len(found_items)):
                    min_price = cls.get_price_article_from_page(found_items[i]["article_detail_url"])
                    if min_price:
                        found_items[i]['min_price'] = min_price
                filtered_items = list(filter(lambda x: x.get('min_price', '') != '', found_items))
                if filtered_items:
                    item_min_price = min(filtered_items, key=lambda x: x['min_price'])
                    # return item_min_price['min_price']
                    cls.append_dp({"auto1": item_min_price['min_price']})
                else:
                    # return item_min_price['min_price']

                    cls.append_dp({"auto1": None})

        except Exception as _ex:
            print(_ex)
            # return None
            ExceptionsLogs.write_log()
            cls.append_dp({"auto1": None})

