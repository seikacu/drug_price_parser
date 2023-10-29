import csv

from selen import get_data as go_selen
from bs4 import BeautifulSoup


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
    if link.find('eapteka'):
        return 1
    elif link.find('apteka'):
        return 2
    elif link.find('zhivika'):
        return 3
    elif link.find('lekkupi'):
        return 4
    elif link.find('maksavit'):
        return 5


def get_csv_file(path, file_name):
    with open(f'{path}{file_name}', newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            city = row[0]
            lat_city = cur_to_lat(f'{city}', t, sep='+')
            link = row[1]
            site = check_site(link)
            is_moscow = check_city(lat_city)
            link_split = link.split('/')
            area = link_split[2]
            if site == 1:
                if is_moscow == 0:
                    link_split.insert(3, lat_city)
                    link = ''
                    for i in link_split:
                        link += i + '/'
                    link = link[:-1]
                go_selen(link, site, is_moscow, city, area)
            elif site == 2:
                pass
            elif site == 3:
                pass
            elif site == 4:
                pass
            elif site == 5:
                pass


def main():
    path = "data/"
    file_name = "example.csv"
    print("start")
    get_csv_file(path, file_name)
    print("end")


if __name__ == '__main__':
    main()
