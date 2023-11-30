import requests
from user_agent import user_agent
from bs4 import BeautifulSoup
from slugify import slugify
import re
from shared_data_pool import DataPool


class AutoostrovBy(DataPool):

    __session = requests.Session()
    __host = 'https://autoostrov.by'
    article = None
    brand = None

    @classmethod
    def __get_html(cls, url: str, method: str = 'get'):
        url = cls.__host + url if cls.__host not in url else url
        request = {
            'get': cls.__session.get(url=url, headers=user_agent),
            'post': cls.__session.post(url=url, headers=user_agent)
        }
        response = request[method]

        if response.status_code == 200:
            return response.text

    @classmethod
    def __reset_article_brand(cls):
        cls.article = None
        cls.brand = None

    @staticmethod
    def __filter_values(value_1, value_2):
        items = [value_1, value_2]
        for i in (0, 1):
            items[i] = slugify(items[i])
            items[i] = items[i].replace('-', '')

        if items[0] in items[1] or items[1] in items[0]:
            return True
        else:
            return False

    @classmethod
    def find_articles(cls, article, brand_name) -> list[dict] | list[None]:
        cls.article = article
        cls.brand = brand_name

        tail_url = f'/search/number/?article={article.replace(" ", "+")}'
        html = cls.__get_html(url=tail_url)
        search_article_url = cls.__get_search_article_url(html)

        if search_article_url:
            param_for_api_request = cls.__get_param_for_api_request(html)
            items_result = cls. __request_to_api_find_valid_articles(param_for_api_request, search_article_url)
            cls.__reset_article_brand()

            return items_result

        else:
            items_result = []
            # find all valid links on articles and iterate
            soup = BeautifulSoup(html, "html.parser")
            a_list = [div.find('a') for div in soup.find_all('div', class_='g-descr-sup-brand')]
            filtered_a_list = [a for a in a_list if cls.__filter_values(a.text, cls.brand)]

            if filtered_a_list:
                for a in filtered_a_list:
                    html = cls.__get_html(url=a['href'])
                    search_article_url = a['href'].replace(cls.__host, '')
                    if search_article_url:
                        param_for_api_request = cls.__get_param_for_api_request(html)
                        items_result.extend(
                            cls.__request_to_api_find_valid_articles(param_for_api_request, search_article_url)
                        )
            cls.__reset_article_brand()

            return items_result

    @staticmethod
    def __get_search_article_url(html):
        soup = BeautifulSoup(html, "html.parser")
        div_m_search = soup.find('div', class_='for-m-search-sort')
        if div_m_search:
            onclick_f_text = div_m_search.find('li').find('a')['onclick']
            if onclick_f_text:
                search_url = re.search(r"'.+?'", onclick_f_text)
                search_url = search_url.group(0).strip("'").rstrip('?')

                return search_url

    @classmethod
    def __get_param_for_api_request(cls, html):
        soup = BeautifulSoup(html, "html.parser")

        scripts = soup.find_all('script')
        for script in scripts:
            script = script.text
            result = re.search(r"&ws-(.*)'", script)
            if result:

                return result.group(0).rstrip("'")

    @classmethod
    def __request_to_api_find_valid_articles(cls, param_for_api_request, search_url):
        result_list = []

        url = search_url + f'?={param_for_api_request}&ajax=reload&resort=all'
        html = cls.__get_html(url=url, method='post')
        soup = BeautifulSoup(html, "html.parser")

        try:
            div_list = \
                [i for i in soup.find_all('div', class_='g-descr-sup-brand') if cls.__filter_values(i.find('a').text, cls.brand)]
        except Exception as _ex:
            print(_ex)

            return result_list

        div_list = [i.parent.parent for i in div_list]
        for item in div_list:
            if not cls.__filter_values(item.find('a', class_='m-article').text, cls.article):
                continue
            brand = item.find('div', class_='g-descr-sup-brand').find('a')
            article_name = item.find('a', class_='m-article')
            article_details_url = item.find('a', class_='m-article')
            price = item.find('span', class_='big-price')
            result_list.append(
                {
                    "brand": brand.text if brand else None,
                    "article_name": article_name.text if article_name else None,
                    "article_details_url": article_details_url['href'] if article_details_url else None,
                    "price": price.text if price else None
                }
            )

        return result_list

    @classmethod
    def main(cls, article, brand_name):
        try:
            found_items = cls.find_articles(article, brand_name)
            if found_items:
                prices_list = [float(i['price']) for i in found_items if i['price']]
                # return min(prices_list)
                cls.append_dp({"avtoostrov": min(prices_list)})

        except Exception as _ex:
            print(_ex)
            # return None
            cls.append_dp({"avtoostrov": None})
