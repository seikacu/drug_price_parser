import platform
import time
import zipfile
import re

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as ex_cond
from webdriver_manager.chrome import ChromeDriverManager

import secure


def set_driver_options(options):
    # безголовый режим браузера
    # options.headless = True
    # options.add_argument('--headless')
    # options.add_argument('--headless=new')
    # options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--deny-permission-prompts")
    # options.add_argument("--enable-strict-powerful-feature-restrictions")
    options.add_argument("--disable-javascript")
    options.add_argument("--disable-geolocation")
    prefs = {
        'profile.default_content_settings.geolocation': 2,
        'profile.managed_default_content_settings.images': 2,
        'profile.managed_default_content_settings.javascript': 2
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


def get_path_webdriver():
    if platform.system() == "Windows":
        return r"C:\WebDriver\chromedriver\chromedriver.exe"
    elif platform.system() == "Linux":
        return "/home/seikacu/webdriver/chromedriver"
    elif platform.system() == "Darwin":
        return "webdriver/chromedriver-macos"
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
    # executable_path=get_path_webdriver())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def get_data(link, site, is_moscow, city, area, check=None):
    driver = None
    try:
        file_name = ""
        link_split = link.split('/')
        if site == 1 and is_moscow == 0:
            file_name = link_split[5]
        if site == 1 and is_moscow == 1:
            file_name = link_split[4]

        driver = get_selenium_driver(True)
        driver.get(link)
        page_content = driver.page_source
        with open(f'data/{file_name}.html', 'w') as file:
            file.write(page_content)
        with open(f"data/{file_name}.html", encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, "lxml")
        if site == 1:
            # Название препарата
            item = ''
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
                        get_data(link, site, is_moscow, city, area, 1)
                else:
                    print("Товар не найден")
                    return
            else:
                item = h1.text
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
            num_rev = re.findall(r'\d+', num_rev_str)[0]
            print(f'Сайт: {area}, Город: {city}, Название: {item}, Стоимость: {price}, Рейтинг: {rating}, Кол-во '
                  f'отзывов: {num_rev}')


        # driver.execute_script("localStorage.setItem('selected_city', 'Москва');")
        time.sleep(1)
    except NoSuchElementException as ex:
        # reason = "Элемент не найден"
        # secure.log.write_log(reason, ex)
        pass
    finally:
        driver.quit()
