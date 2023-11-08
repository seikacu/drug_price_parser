import platform
import time
import zipfile
import re

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc

import secure
from db_sql import insert_to_table, check_url_in_bd


def set_driver_options(options):
    # безголовый режим браузера
    # options.headless = True
    # options.add_argument('--headless=new')
    options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    # options.add_argument("--deny-permission-prompts")
    # options.add_argument("--enable-strict-powerful-feature-restrictions")
    # options.add_argument("--disable-javascript")
    options.add_argument("--disable-geolocation")
    prefs = {
        'profile.default_content_settings.geolocation': 2,
        'profile.managed_default_content_settings.images': 2,
        # 'profile.managed_default_content_settings.javascript': 2
    }
    options.add_experimental_option("prefs", prefs)
    # options.add_argument("--deny-permission-prompts")
    options.add_argument("--disable-blink-features=AutomationControlled")


def get_path_profile():
    if platform.system() == "Windows":
        return r"C:\WebDriver\chromedriver\user"
    elif platform.system() == "Linux":
        return "/home/seikacu/webdriver/user"
    elif platform.system() == "Darwin":
        return "webdriver/chromedriver-macos/user"
    else:
        raise Exception("Unsupported platform!")


def get_selenium_driver(use_proxy=False):
    options = webdriver.ChromeOptions()
    set_driver_options(options)

    if use_proxy:
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        plugin_file = 'proxy_auth_plugin.zip'

        with zipfile.ZipFile(plugin_file, 'w') as zp:
            zp.writestr('manifest.json', secure.manifest_json_1)
            zp.writestr('background.js', secure.background_js_1)

        options.add_extension(plugin_file)

    user_agent = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/116.0.5845.967 YaBrowser/23.9.1.967 Yowser/2.5 Safari/537.36")
    options.add_argument(f'--user-agent={user_agent}')

    caps = DesiredCapabilities().CHROME
    caps['pageLoadStrategy'] = 'eager'

    service = Service(ChromeDriverManager().install(), desired_capabilities=caps)
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def get_data(connection, driver: webdriver.Chrome, link, site, is_moscow, city, lat_city, site_name, csv_name,
             check=None):
    try:
        file_name = ""
        link_split = link.split('/')
        if site == 1 and is_moscow == 0:
            file_name = link_split[5]
        elif (site == 1 and is_moscow == 1) or site == 4:
            file_name = link_split[4]

        driver.get(link)

        if site == 1:
            page_content = driver.page_source
            with open(f'data/{file_name}.html', 'w') as file:
                file.write(page_content)
            with open(f"data/{file_name}.html", encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, "lxml")
            # Название препарата
            product_name = ''
            h1 = soup.find('h1')
            if h1 is None:
                if check is None:
                    new_city = f'city-{link_split[3]}'
                    link_split[3] = new_city
                    link = ''
                    for i in link_split:
                        link += i + '/'
                    link = link[:-1]
                    if 'city-' in link_split[3]:
                        if check_url_in_bd(connection, link):
                            print(f'url: {link} уже есть в БД')
                            return
                        get_data(connection, driver, link, site, is_moscow, city, site_name, csv_name, 1)
                else:
                    print("Товар не найден")
                    insert_to_table(connection, link, city, 'Товар не найден', '', '', '',
                                    site_name, csv_name)
                    return
            else:
                product_name = h1.text
            price_class = soup.find('span', {'class': 'offer-tools__price_num-strong'})
            if price_class is None:
                return
            # Стоимость препарата
            price = price_class.get('data-price')
            rating_div = soup.find('div', class_='rating__common').find('div', class_='rating')
            # Рейтинг
            rating = ''
            if rating_div is not None:
                rating_class = rating_div.get_attribute_list('class')
                rating = rating_class[1][-1:]
            num_rev_str = soup.find('span', {'class': 'rating__common-subtitle'}).text
            # Количество отзывов
            count = re.findall(r'\d+', num_rev_str)[0]
            print(f'Сайт: {site_name}, Город: {city}, Название: {product_name}, Стоимость: {price},'
                  f' Рейтинг: {rating}, Кол-во отзывов: {count}')
            insert_to_table(connection, link, city, product_name, price, rating, count,
                            site_name, csv_name)
        elif site == 4:
            WebDriverWait(driver, 15).until(
                expected_conditions.presence_of_element_located(
                    (By.CLASS_NAME, "header-top-container-changer")
                ))

            cook_but = driver.find_element(By.CLASS_NAME, 'cookie-accept-button')
            cook_but.click()
            select_city = driver.find_element(By.XPATH, f"//a[contains(@data-location-code,'{lat_city}')]")
            if select_city is None:
                print("В данном городе нет аптек")
            else:
                driver.execute_script("arguments[0].click();", select_city)
                time.sleep(1)
                page_content = driver.page_source
                with open(f'data/{file_name}.html', 'w') as file:
                    file.write(page_content)
                with open(f"data/{file_name}.html", encoding="utf-8") as file:
                    src = file.read()
                soup = BeautifulSoup(src, "lxml")
                product_name = soup.find('h1').text
                price = soup.find('span', {'class': 'price'}).text
                rating = ''
                count = ''
                print(f'Сайт: {site_name}, Город: {city}, Название: {product_name}, Стоимость: {price},'
                      f' Рейтинг: {rating}, Кол-во отзывов: {count}')
                insert_to_table(connection, link, city, product_name, price, rating, count,
                                site_name, csv_name)

        time.sleep(1)

    except NoSuchElementException as ex:
        print(ex)
        reason = "Элемент не найден"
        secure.log.write_log(reason, ex)
        pass
