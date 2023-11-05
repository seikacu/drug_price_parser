import csv
import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup

import secure
from db_sql import create_table, connect_db, check_exist_table, get_result, check_url_in_bd, insert_to_table
from selen import get_data as go_selen, get_selenium_driver


def cur_to_lat(string, t, sep='-'):
    new_string = ''
    for cur in string.lower():
        if cur in list(t.keys()):
            new_string += t[cur]
        elif cur == " ":
            new_string += sep

    return new_string


t = {'ё': 'yo', 'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ж': 'zh', 'з': 'z', 'і': 'i',
     'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
     'у': 'u', 'ф': 'f', 'х': 'h', 'ц ': 'c', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'и': 'i', 'ь': '',
     'э': 'e', 'ю': 'yu', 'я': 'ya'}


def check_city(city: str):
    if city == 'moskva':
        return 1
    else:
        return 0


def check_site(link: str):
    if 'eapteka' in link:
        return 1
    elif 'apteka' in link:
        return 2
    elif 'zhivika' in link:
        return 3
    elif 'lekkupi' in link:
        return 4
    elif 'maksavit' in link:
        return 5


def start(path, file_name):
    connection = None
    driver = None
    try:
        connection = connect_db()
        connection.autocommit = True
        if check_exist_table(connection) is False:
            create_table(connection)
        if not os.path.exists("result"):
            os.mkdir("result")
        dt = datetime.now()
        name_csv = dt.strftime('%Y-%m-%d')
        with open(f"result/{name_csv}.csv", "w", newline='', encoding="utf-8") as file:
            writer = csv.writer(file, delimiter='\t')
            writer.writerow(
                (
                    "id",
                    "url",
                    "city",
                    "name_product",
                    "price",
                    "rating",
                    "count",
                    "site",
                    "file_name"
                )
            )

        driver = get_selenium_driver(True)
        with open(f'{path}{file_name}', newline='', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            csv_name = file_name[:-4]
            for row in reader:
                city = row[0]
                lat_city = cur_to_lat(f'{city}', t, sep='+')
                link = row[1]
                site = check_site(link)
                # site = 3
                link_split = link.split('/')
                site_name = link_split[2]
                if site == 1:
                    is_moscow = check_city(lat_city)
                    if is_moscow == 0:
                        link_split.insert(3, lat_city)
                        link = ''
                        for i in link_split:
                            link += i + '/'
                        link = link[:-1]
                    if check_url_in_bd(connection, link):
                        print(f'url: {link} уже есть в БД')
                        continue
                    go_selen(connection, driver, link, site, is_moscow, city, site_name, csv_name)
                elif site == 2:
                    if check_url_in_bd(connection, link):
                        print(f'url: {link} уже есть в БД')
                        continue
                    good_str = link_split[4]
                    good_split = good_str.split('-')
                    good_id = good_split[-1]

                    headers = {
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0',
                        'Accept': 'application/json, text/plain, */*',
                        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Origin': 'https://apteka.ru',
                        'Connection': 'keep-alive',
                        'Referer': 'https://apteka.ru/',
                    }
                    params = {
                        'ids': [
                            f'{good_id}',
                        ],
                        'cityUrl': f'{lat_city}',
                    }

                    r = requests.get('https://api.apteka.ru/Search/GoodsById', params=params, headers=headers,
                                     proxies=secure.proxies)
                    json_data = r.json()

                    find = json_data['totalCount']
                    product_name = 'Товар не найден'
                    price = '0'
                    rating = '0'
                    count = '0'
                    if find > 0:
                        result = json_data['result']
                        for line in result:
                            item_info = line['uniqueItemInfo']
                            item_info_2 = line['tradeName']
                            good_naming = item_info['goodNaming']
                            product_name = good_naming['tradeName']
                            if len(item_info_2) > 1 and str(item_info_2).lower() not in str(product_name).lower():
                                product_name += f' {item_info_2}'
                            price = str(line['minPrice'])
                        r = requests.get(link, headers=headers, proxies=secure.proxies)
                        soup = BeautifulSoup(r.content, "lxml")
                        rating_doc = soup.find('span', {'class': 'ItemRating__label'})
                        if rating_doc is not None:
                            rating = rating_doc.text
                        count_doc = soup.find('span', {'itemprop': 'reviewCount'})
                        if count_doc is not None:
                            count = count_doc.text
                    else:
                        pass
                    print(f'Сайт: {site_name}, Город: {city}, Название: {product_name}, Стоимость: {price},'
                          f' Рейтинг: {rating}, Кол-во отзывов: {count}')
                    insert_to_table(connection, link, city, product_name, price, rating, count,
                                    site_name, csv_name)
                elif site == 3:
                    if check_url_in_bd(connection, link):
                        print(f'url: {link} уже есть в БД')
                        continue
                        pass

                elif site == 4:
                    if check_url_in_bd(connection, link):
                        print(f'url: {link} уже есть в БД')
                        continue
                        pass

                elif site == 5:
                    if check_url_in_bd(connection, link):
                        print(f'url: {link} уже есть в БД')
                        continue
                        pass

    except Exception as _ex:
        secure.log.write_log("create_table_ads ", _ex)
        print("Error while working with PostgreSQL", _ex)
    finally:
        if driver:
            driver.quit()
        if connection:
            connection.close()
            print("[INFO] PostgreSQL connection closed")


def main():
    path = "data/"
    file_name = "example3.csv"
    print("start")
    start(path, file_name)
    get_result(file_name[:-4])
    print("end")


if __name__ == '__main__':
    main()
