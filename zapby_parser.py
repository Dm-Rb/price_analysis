import requests
from user_agent import user_agent
from bs4 import BeautifulSoup
from slugify import slugify
from shared_data_pool import DataPool


class ZapBy(DataPool):

    __session = requests.Session()
    __host = 'https://zap.by'
    redirection = False

    @classmethod
    def __get_html(cls, url: str, host: bool = True, json: bool = False):
        response = cls.__session.get(url=cls.__host + url if host else url, headers=user_agent)
        if response.status_code == 200:
            if json:
                return response.json()
            else:
                return response.text

    @classmethod
    def search_articles_url(cls, article, brand_name):

        tail_url = f'/carparts/search/{article}/'
        html = cls.__get_html(url=tail_url)
        page_items = cls.__parse_articles_brands_url(html)
        ajax_items = cls.__get_ajax_content(article)
        [page_items.append(i) for i in ajax_items if i not in page_items]
        filtered_items = [i for i in page_items if cls.filter_values(i['brand'], brand_name)]

        return filtered_items

    @classmethod
    def __get_ajax_content(cls, article, brand=''):
        # request to api: #
        # if brand==False-> get brand name/article name/url to page #
        # if brand==True-> get price article from analog-group #

        result_list = []
        for value in ('3', '6'):
            if not brand:
                api_url = f"/carparts/info/ws?id={value}&article={article}&brand={brand}&type=1&view=list&exact_match=0"
                response_json = cls.__get_html(url=api_url, json=True)
                items = cls.__parse_ajax_content_abu(response_json)

            else:
                api_url = f"/carparts/info/ws?id={value}&article={article}&brand={brand}&type=0&view=list&exact_match=0"
                response_json = cls.__get_html(url=api_url, json=True)
                items = cls.__parse_ajax_content_pa(response_json, brand)
            result_list.extend(items)

        return result_list

    @classmethod
    def __parse_ajax_content_abu(cls, response_json) -> list:
        # get brand/article/url
        result_list = []
        if response_json['success'] and response_json['data']['parts']:

            keys = response_json['data']['parts'].keys()
            if keys:
                parts = response_json['data']['parts']
                for key in keys:
                    item = cls.__parse_articles_brands_url(html=parts[key]['block'])
                    result_list.extend(item)
        return result_list

    @classmethod
    def __parse_ajax_content_pa(cls, response_json, brand):
        # get price article fom analogs group
        result_list = []
        if response_json['success'] and response_json['data']['parts']:

            keys = response_json['data']['parts'].keys()
            if keys:
                parts = response_json['data']['parts']
                for key in keys:
                    if slugify(brand).replace('-', '') in slugify(key).replace('-', ''):
                        try:
                            soup = BeautifulSoup(parts[key]['prices'], 'html.parser')
                            register_price = soup.find_all('tr', class_='pr-ws')
                            [result_list.append(i['data-price'].replace(' ', '')) for i in register_price]

                        except Exception as _ex:
                            print(_ex)
                            continue
        return result_list

    @classmethod
    def __parse_articles_brands_url(cls, html):
        result_list = []
        soup = BeautifulSoup(html, 'html.parser')
        tr_list = soup.find_all('tr', class_='pointer')
        if tr_list:
            for tr in tr_list:
                try:
                    brand_name = tr.find('td').find('strong').text
                    article = tr.find('td').text.replace(brand_name, '').strip()
                    url = tr.find("td", class_='text-right').find('a')['href']
                    result_list.append(
                        {
                            "brand": brand_name,
                            "article": article,
                            "page_url": url
                        }
                    )
                except Exception as _ex:
                    print(_ex)
                    continue

        return result_list

    @staticmethod
    def filter_values(value_1: str, value_2: str):

        items = [value_1, value_2]
        for i in (0, 1):
            items[i] = items[i].replace('Ö', 'OE')
            items[i] = slugify(items[i])
            items[i] = items[i].replace('-', '')
            items[i] = items[i].replace('_', '')
            items[i] = items[i].replace('/', '')
            items[i] = items[i].replace('\\', '')

        if items[0] in items[1] or items[1] in items[0]:
            return True
        else:
            return False


    @classmethod
    def get_article_price_from_page(cls, article, brand, url):
        html = cls.__get_html(url)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            # пробуем дёрнуть цену прямо из отрендереной страницы c типом проверено
            wrapper_div = soup.find('div', class_='product-view_product')
            if wrapper_div:
                price_basket = wrapper_div.find('strong', class_='font-38')
                if price_basket:
                    return price_basket.text

            # делаем запрос к апи и получаем список аналогов с прайсами
            price_list = cls.__get_ajax_content(article, brand)
            if price_list:
                return min(price_list)

    @classmethod
    def get_min_price(cls, article_items):
        prices = []
        for item in article_items:
            if item["page_url"][0] != '/':
                continue
            article = item['article']
            brand = item['brand']
            url = item["page_url"]
            price = cls.get_article_price_from_page(article, brand, url)
            if price:
                prices.append(float(price))
        if prices:
            return min(prices)



    @classmethod
    def main(cls, article, brand):
        result = {"zap": None}
        try:
            article_items = cls.search_articles_url(article, brand)
            min_price = cls.get_min_price(article_items)
            if min_price:
                # return result
                result["zap"] = float(min_price)
                cls.append_dp(result)
            else:
                url = f"/{slugify(brand).replace(' ','')}/{slugify(article).replace(' ','')}"
                price = cls.get_article_price_from_page(article, brand, url)
                if price:
                    result["zap"] = float(price.replace(' ', ''))
                    # return result
                    cls.append_dp(result)
                else:
                    cls.append_dp(result)

        except Exception as _ex:
            print(_ex)
            cls.append_dp(result)
            # return result

# ZapBy.main('F 026 002 572', 'BOSCH')
# print(DataPool.prices_pool)