import csv
import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup

import secure
from db_sql import create_table, connect_db, check_exist_table, get_result, check_url_in_bd, insert_to_table
from selen import get_data as go_selen, get_selenium_driver
from requests_html import HTMLSession


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
                    session = HTMLSession()

                    cookies = {
                        'XSRF-TOKEN': 'eyJpdiI6IkRyQjJRSWN4Q081ZkRyOUtBRWRCeXc9PSIsInZhbHVlIjoiSVNuczZxa0VUR3N4a1wvbTFPVGR0UXJCM0cyUVwvbExvMjBWRDVuRmo0ZUZEV3NwaUJTaFJQV2s2b1JheVFHc05iIiwibWFjIjoiZTg3NWQwN2Y4NTA1M2MwZWY2MGY2ZjkzOWRlMzRhYWI3ZTdkMzcxNGE5MjE4NDgxMjU0ODA3NGNiZGQ2NDM5YiJ9',
                        'laravel_session': 'eyJpdiI6IlRHTFZQcnozTEdUTlNsbmlBZnZMVWc9PSIsInZhbHVlIjoiYTg5QllqK3o1NHZ2eVFyMUF4eE1IQThVdVlPRVB1MjdXcnRoWG84NzJUdFgrM2hVckJZNk1sRXNSSENvUlhXbSIsIm1hYyI6IjZiYWM1YTUyNWFiZDRmOGRmNzI4YmMxYjM0N2QzM2IwYTcyMGEwM2RjZDdkZmJkMmUzOTM4YjMyNjFjNGQ4ZjIifQ%3D%3D',
                        'session_id': 'eyJpdiI6ImdvZGxjVWRlZEpoNnFnKzhUcnpJRmc9PSIsInZhbHVlIjoiNTl6c2NnTjAwUnl1U2J4dUZCakxuUGJ4ZlpLK2dkMUtJUFY5Qk1yeU1qcXNTTEMrcVRtTmRtMnNadnNrS25Oa3hBOWhjZ0VTT2lvSk1qZ2VHTXVCekE9PSIsIm1hYyI6ImNmZTI1YzdmMzQzMDM2Y2UwMjBlMDlmZGQwN2Y2ZDQ2ZTA0OTRkZGM2MGFlZDg1ZjhmZWI3NDJlM2U5NjUxMWQifQ%3D%3D',
                        'QtaPrHFKA3Te1Rh70k2JHGujJaOk6SuqlIjGTYZq': 'eyJpdiI6IlFhdlJJb0pDR1BGNXE3RmF0cVhYNHc9PSIsInZhbHVlIjoidW9EV3BaRlhVSVwvRUVkY2JrU0FFRGhmbE9MR3A1cDBoUCtFeE91bnV1Z0o0a3RoQjVQZFdkeHNTYnlMUzMxcTU2SDJ2RGRpWEc3SWJWeWsrOW9Tc0ZSWFU0QU4zcVwvcVJUN0NlN1wvTWNuXC9pTkZwWGlYMVZnTVwvaVwvcEJ0YVpZZWlONFZQeU1FOGhqZmxcL0l3Y083bFpXckwzY0xwblBnaXdWODg4WEpcLzcxdnNYRVkxd0NDc1Jqd0JiSFZBZFJRQ1VzbmNxMm9FZjlUK09vazBPQ28zTVk3XC9nb1BjMDV6UHJjQUFHSXorUDB6NVprWFhEam9FOGVGUUhoZmMxRVJZQjdpMTFIOGpLeXVLZTVvWmZoMTdhczV5ZFwvT0gxeE5nbm00dkY1K0Z5UklPbEcxVFNNXC9vaHdKTzJzbEJKZVRIMmt6S1U5bTRUVFBpQXkxZ1IzVWFZZzhNMExMc1lVYUc0N0F5YXVPWnB6c0JudnZRS1NrNzJCS2VmSlN2MlwvblVwU3JlQXlQaE9vNHpLTzF2RU5PSnNyWCtkWkQxMEJLcDhqeTllQjJvZDkrYThcL1BqN3JGdEdETzBTNVRtWHVKMVwvUHNqc0l4NG11SmhUYW5tUzI3dGJDa29maUVcL2orTDIzWFY3WUJcL1N6V2IyeTFHNkRhRGVjUmhSZXhkSFZFWklaaHZSQ0dpMmRVK010XC9KVHNxWTdVTlJsZURzQUxzUVZxTWRoYUw1dWljeUQ3RUJFSmhqdHJyMXdzdVpISmc4QloiLCJtYWMiOiI1NjFiZmY3NjJkYTVkZDMzZjlkZGIxNmM0OTFlYmI3YmY0OTU5MDlmZTgzMjIyZDM1YjkwZGRlZTY0NDVhOWFkIn0%3D',
                        '_ga_YEDTZMW12Q': 'GS1.1.1698782063.2.1.1698783381.33.0.0',
                        '_ga': 'GA1.1.575298000.1698765033',
                        '_gid': 'GA1.2.627001749.1698765034',
                        'qrator_ssid': '1698782060.407.CWiwWLUDDPuy8oXi-l4lopqamqeltbvkp1k32svafnjaur5ca',
                        'qrator_jsid': '1698782060.103.ErO8zdmjT0RT3z8E-rjehijid3dm3r6qajlcr01u4908u95sh',
                        # 'cityId': '148',
                        'zhToken': 'RFIWND7TSTAIXX5CDBFSXZK4FCC43PKEDKYONHBQWROI6RALZSJQ',
                    }

                    headers = {
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
                        # 'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        # 'Cookie': 'XSRF-TOKEN=eyJpdiI6IkRyQjJRSWN4Q081ZkRyOUtBRWRCeXc9PSIsInZhbHVlIjoiSVNuczZxa0VUR3N4a1wvbTFPVGR0UXJCM0cyUVwvbExvMjBWRDVuRmo0ZUZEV3NwaUJTaFJQV2s2b1JheVFHc05iIiwibWFjIjoiZTg3NWQwN2Y4NTA1M2MwZWY2MGY2ZjkzOWRlMzRhYWI3ZTdkMzcxNGE5MjE4NDgxMjU0ODA3NGNiZGQ2NDM5YiJ9; laravel_session=eyJpdiI6IlRHTFZQcnozTEdUTlNsbmlBZnZMVWc9PSIsInZhbHVlIjoiYTg5QllqK3o1NHZ2eVFyMUF4eE1IQThVdVlPRVB1MjdXcnRoWG84NzJUdFgrM2hVckJZNk1sRXNSSENvUlhXbSIsIm1hYyI6IjZiYWM1YTUyNWFiZDRmOGRmNzI4YmMxYjM0N2QzM2IwYTcyMGEwM2RjZDdkZmJkMmUzOTM4YjMyNjFjNGQ4ZjIifQ%3D%3D; session_id=eyJpdiI6ImdvZGxjVWRlZEpoNnFnKzhUcnpJRmc9PSIsInZhbHVlIjoiNTl6c2NnTjAwUnl1U2J4dUZCakxuUGJ4ZlpLK2dkMUtJUFY5Qk1yeU1qcXNTTEMrcVRtTmRtMnNadnNrS25Oa3hBOWhjZ0VTT2lvSk1qZ2VHTXVCekE9PSIsIm1hYyI6ImNmZTI1YzdmMzQzMDM2Y2UwMjBlMDlmZGQwN2Y2ZDQ2ZTA0OTRkZGM2MGFlZDg1ZjhmZWI3NDJlM2U5NjUxMWQifQ%3D%3D; QtaPrHFKA3Te1Rh70k2JHGujJaOk6SuqlIjGTYZq=eyJpdiI6IlFhdlJJb0pDR1BGNXE3RmF0cVhYNHc9PSIsInZhbHVlIjoidW9EV3BaRlhVSVwvRUVkY2JrU0FFRGhmbE9MR3A1cDBoUCtFeE91bnV1Z0o0a3RoQjVQZFdkeHNTYnlMUzMxcTU2SDJ2RGRpWEc3SWJWeWsrOW9Tc0ZSWFU0QU4zcVwvcVJUN0NlN1wvTWNuXC9pTkZwWGlYMVZnTVwvaVwvcEJ0YVpZZWlONFZQeU1FOGhqZmxcL0l3Y083bFpXckwzY0xwblBnaXdWODg4WEpcLzcxdnNYRVkxd0NDc1Jqd0JiSFZBZFJRQ1VzbmNxMm9FZjlUK09vazBPQ28zTVk3XC9nb1BjMDV6UHJjQUFHSXorUDB6NVprWFhEam9FOGVGUUhoZmMxRVJZQjdpMTFIOGpLeXVLZTVvWmZoMTdhczV5ZFwvT0gxeE5nbm00dkY1K0Z5UklPbEcxVFNNXC9vaHdKTzJzbEJKZVRIMmt6S1U5bTRUVFBpQXkxZ1IzVWFZZzhNMExMc1lVYUc0N0F5YXVPWnB6c0JudnZRS1NrNzJCS2VmSlN2MlwvblVwU3JlQXlQaE9vNHpLTzF2RU5PSnNyWCtkWkQxMEJLcDhqeTllQjJvZDkrYThcL1BqN3JGdEdETzBTNVRtWHVKMVwvUHNqc0l4NG11SmhUYW5tUzI3dGJDa29maUVcL2orTDIzWFY3WUJcL1N6V2IyeTFHNkRhRGVjUmhSZXhkSFZFWklaaHZSQ0dpMmRVK010XC9KVHNxWTdVTlJsZURzQUxzUVZxTWRoYUw1dWljeUQ3RUJFSmhqdHJyMXdzdVpISmc4QloiLCJtYWMiOiI1NjFiZmY3NjJkYTVkZDMzZjlkZGIxNmM0OTFlYmI3YmY0OTU5MDlmZTgzMjIyZDM1YjkwZGRlZTY0NDVhOWFkIn0%3D; _ga_YEDTZMW12Q=GS1.1.1698782063.2.1.1698783381.33.0.0; _ga=GA1.1.575298000.1698765033; _gid=GA1.2.627001749.1698765034; qrator_ssid=1698782060.407.CWiwWLUDDPuy8oXi-l4lopqamqeltbvkp1k32svafnjaur5ca; qrator_jsid=1698782060.103.ErO8zdmjT0RT3z8E-rjehijid3dm3r6qajlcr01u4908u95sh; cityId=148; zhToken=RFIWND7TSTAIXX5CDBFSXZK4FCC43PKEDKYONHBQWROI6RALZSJQ',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-User': '?1',
                    }

                    r = session.get(link, cookies=cookies, headers=headers, proxies=secure.proxies).text
                    print(r)

                elif site == 4:
                    if check_url_in_bd(connection, link):
                        print(f'url: {link} уже есть в БД')
                        continue

                    session = HTMLSession()

                    cookies = {
                        'cf_clearance': 'HRubcUejoIwRf9mC946dqMFyPY7cXvFt88ghB7Udd_k-1698784758-0-1-bef57b7f.aeb984cf.e9f4249f-150.0.0',
                        '_pharmacy_frontend': 'gvh7kqpd6j8ttmlrm2ldgc6d7u',
                        '_guest_code': '7de3a08be05d230823590b8d9afb8dc04beb887f3b7b5a457dabf385646c1581a%3A2%3A%7Bi%3A0%3Bs%3A11%3A%22_guest_code%22%3Bi%3A1%3Bs%3A255%3A%22FsAc51Jdt2E8_CE8Egwdpze1l-hLOBL7JpKEuBROl3tlqWem9bZGfz-RT5mqqFR9jm2ejjo_11pjC3dramzP1sEVs5TJ4wnC3bO0TvJF9pdBDgbmmit68ueoPndmarAbrXg4RF_Ejtc5KEpNmNvhEwqz8Y00-HphkQsPsF5CQT2_laCWJRVzeNv6LXeERvtUMCPlrdQsktMZsoElbqctSkN3zpGMjB0q-V8n0TomLN-ZW19nnV1dGZuhb0ljsu5%22%3B%7D',
                        '_csrf_frontend': '306c5440f1aa66ae3cd674458e24fea540f621c451aa0f76deb91415e70f4c3ba%3A2%3A%7Bi%3A0%3Bs%3A14%3A%22_csrf_frontend%22%3Bi%3A1%3Bs%3A32%3A%22lxFJwskQlNvpOps-xUi4x4kW2XzXtsGZ%22%3B%7D',
                        '_ga_6GV523EMY1': 'GS1.1.1698784770.1.0.1698784770.0.0.0',
                        '_ga': 'GA1.2.2058882064.1698784770',
                        '_gid': 'GA1.2.1081109923.1698784771',
                        '_ga_WX7XBZNF2R': 'GS1.2.1698784770.1.0.1698784770.0.0.0',
                        '_cookie_accepted_at': 'f60cad239d1172930adbc480a06ab659b88f9762aa5f5ec8437739e23a2db941a%3A2%3A%7Bi%3A0%3Bs%3A19%3A%22_cookie_accepted_at%22%3Bi%3A1%3Bs%3A19%3A%222023-11-01%2003%3A40%3A09%22%3B%7D',
                    }

                    headers = {
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
                        # 'Accept-Encoding': 'gzip, deflate, br',
                        'Alt-Used': 'lekkupi.ru',
                        'Connection': 'keep-alive',
                        'Referer': 'https://lekkupi.ru/catalog/kagocel_tbl_12mg_no20',
                        # 'Cookie': 'cf_clearance=HRubcUejoIwRf9mC946dqMFyPY7cXvFt88ghB7Udd_k-1698784758-0-1-bef57b7f.aeb984cf.e9f4249f-150.0.0; _pharmacy_frontend=gvh7kqpd6j8ttmlrm2ldgc6d7u; _guest_code=7de3a08be05d230823590b8d9afb8dc04beb887f3b7b5a457dabf385646c1581a%3A2%3A%7Bi%3A0%3Bs%3A11%3A%22_guest_code%22%3Bi%3A1%3Bs%3A255%3A%22FsAc51Jdt2E8_CE8Egwdpze1l-hLOBL7JpKEuBROl3tlqWem9bZGfz-RT5mqqFR9jm2ejjo_11pjC3dramzP1sEVs5TJ4wnC3bO0TvJF9pdBDgbmmit68ueoPndmarAbrXg4RF_Ejtc5KEpNmNvhEwqz8Y00-HphkQsPsF5CQT2_laCWJRVzeNv6LXeERvtUMCPlrdQsktMZsoElbqctSkN3zpGMjB0q-V8n0TomLN-ZW19nnV1dGZuhb0ljsu5%22%3B%7D; _csrf_frontend=306c5440f1aa66ae3cd674458e24fea540f621c451aa0f76deb91415e70f4c3ba%3A2%3A%7Bi%3A0%3Bs%3A14%3A%22_csrf_frontend%22%3Bi%3A1%3Bs%3A32%3A%22lxFJwskQlNvpOps-xUi4x4kW2XzXtsGZ%22%3B%7D; _ga_6GV523EMY1=GS1.1.1698784770.1.0.1698784770.0.0.0; _ga=GA1.2.2058882064.1698784770; _gid=GA1.2.1081109923.1698784771; _ga_WX7XBZNF2R=GS1.2.1698784770.1.0.1698784770.0.0.0; _cookie_accepted_at=f60cad239d1172930adbc480a06ab659b88f9762aa5f5ec8437739e23a2db941a%3A2%3A%7Bi%3A0%3Bs%3A19%3A%22_cookie_accepted_at%22%3Bi%3A1%3Bs%3A19%3A%222023-11-01%2003%3A40%3A09%22%3B%7D',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'same-origin',
                        'Sec-Fetch-User': '?1',
                        # Requests doesn't support trailers
                        # 'TE': 'trailers',
                    }

                    # r = requests.get(link, cookies=cookies, headers=headers, proxies=secure.proxies)
                    r = session.get(link, cookies=cookies, headers=headers, proxies=secure.proxies)
                    r.html.render()
                    print(r.text)

                elif site == 5:
                    if check_url_in_bd(connection, link):
                        print(f'url: {link} уже есть в БД')
                        continue
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
    file_name = "example5.csv"
    print("start")
    start(path, file_name)
    get_result(file_name[:-4])
    print("end")


if __name__ == '__main__':
    main()
