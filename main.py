import csv
import os
from datetime import datetime
from os import listdir
from os.path import isfile, join
from pathlib import Path
from shutil import rmtree

import secure
from db_sql import (create_table, connect_db, check_exist_table, get_result, check_url_in_bd,
                    insert_main_data, get_main_data, delete_table, delete_data_from_table)
from selen import get_selenium_driver, get_data


def cur_to_lat(string, sep='-'):
    t = {'ё': 'yo', 'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ж': 'zh', 'з': 'z', 'і': 'i',
         'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
         'у': 'u', 'ф': 'f', 'х': 'h', 'ц ': 'c', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'и': 'i', 'ь': '',
         'э': 'e', 'ю': 'yu', 'я': 'ya'}
    new_string = ''
    for cur in string.lower():
        if cur in list(t.keys()):
            new_string += t[cur]
        elif cur == " ":
            new_string += sep
    return new_string


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


def start(path, files):
    connection = None
    driver = None
    try:
        if not os.path.exists('result'):
            os.mkdir('result')
        if not os.path.exists('data/wrk'):
            os.mkdir(os.path.join('data', 'wrk'))
        connection = connect_db()
        connection.autocommit = True
        if check_exist_table(connection) is False:
            create_table(connection)

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
        for file in files:
            with open(f'{path}{file}', newline='', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter='\t')
                csv_name = file[:-4]
                for row in reader:
                    city = row[0]
                    link = row[1]
                    link_split = link.split('/')
                    site_name = link_split[2]
                    if check_url_in_bd(connection, link, csv_name):
                        print(f'url: {link} from file: {csv_name} уже есть в БД')
                        continue
                    insert_main_data(connection, link, city, site_name, csv_name)
        for file in files:
            driver = get_selenium_driver(False, True)
            csv_name = file[:-4]
            main_data = get_main_data(connection, csv_name)
            for data in main_data:
                id_db = data[0]
                link = data[1]
                city = data[2]
                site_name = data[3]

                lat_city = cur_to_lat(f'{city}', sep='+')
                link_split = link.split('/')
                site = check_site(link)

                get_data(connection, driver, link_split, id_db, link, site, city, lat_city,
                         site_name, csv_name)

    except Exception as _ex:
        secure.log.write_log("start ", _ex)
        print("start ", _ex)
    finally:
        if driver:
            driver.quit()
        if connection:
            connection.close()
            print("[INFO] PostgreSQL connection closed")


def get_files(path):
    return [f for f in listdir(path) if isfile(join(path, f))]


def del_trash(path):
    for path in Path(f'{path}wrk').iterdir():
        if path.is_dir():
            rmtree(path)
        else:
            path.unlink()
    print('The garbage has been cleaned :)')


def main():
    path = 'data/'
    files = get_files(path)
    print("start")
    start(path, files)
    get_result(files)
    del_trash(path)
    print('end')
    # delete_table()
    # delete_data_from_table(files)


if __name__ == '__main__':
    main()
