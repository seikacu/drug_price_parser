import time
import zipfile
import re

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

import secure
from db_sql import update_rec


def check_city(city: str):
    if city == 'moskva':
        return 1
    else:
        return 0


def set_driver_options(options, js):
    # безголовый режим браузера
    # options.headless = True
    # options.add_argument('--headless=new')
    options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    # options.add_argument("--deny-permission-prompts")
    # options.add_argument("--enable-strict-powerful-feature-restrictions")
    options.add_argument("--disable-geolocation")
    if js:
        options.add_argument("--disable-javascript")
        prefs = {
            'profile.default_content_settings.geolocation': 2,
            'profile.managed_default_content_settings.images': 2,
            'profile.managed_default_content_settings.javascript': 2
        }
    else:
        prefs = {
            'profile.default_content_settings.geolocation': 2,
            'profile.managed_default_content_settings.images': 2,
            'profile.managed_default_content_settings.javascript': 1
        }
    options.add_experimental_option("prefs", prefs)
    # options.add_argument("--deny-permission-prompts")
    options.add_argument("--disable-blink-features=AutomationControlled")


def get_selenium_driver(js, use_proxy):
    options = webdriver.ChromeOptions()
    set_driver_options(options, js)

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


def get_data(connection, driver: webdriver.Chrome, link_split, id_db, link, site, city, lat_city,
             site_name, csv_name, check=None):
    try:

        driver.get(link)

        product_name = 'Товар не найден'
        price = '0'
        rating = '0'
        count = '0'

        if site == 1:

            link = driver.current_url
            link_split = link.split('/')
            if check is None and len(link_split) == 7:
                link_split.pop(3)
                link = ''
                for i in link_split:
                    link += i + '/'
                link = link[:-1]

            is_moscow = check_city(lat_city)

            if check is None and is_moscow == 0:
                link_split.insert(3, lat_city)
                link = ''
                for i in link_split:
                    link += i + '/'
                link = link[:-1]

            src_name = ''
            if is_moscow == 0:
                src_name = link_split[5]
            elif is_moscow == 1:
                src_name = link_split[4]
            if check is None:
                driver.get(link)
            soup = get_soup(src_name, driver.page_source)
            h1 = soup.find('h1')
            if h1:
                product_name = h1.text
            else:
                if check == 1:
                    update_rec(connection, id_db, product_name, price, rating, count)
                    return
                else:
                    new_city = f'city-{link_split[3]}'
                    link_split[3] = new_city
                    link = ''
                    for i in link_split:
                        link += i + '/'
                    link = link[:-1]
                    get_data(connection, driver, link_split, id_db, link, site, city,
                             lat_city, site_name, csv_name, 1)
            if h1 is None:
                return
            price_class = soup.find('span', {'class': 'offer-tools__price_num-strong'})
            if price_class:
                price = price_class.get('data-price')
            rating_div = soup.find('div', class_='rating__common').find('div', class_='rating')
            if rating_div:
                rating_class = rating_div.get_attribute_list('class')
                rating = rating_class[1][-1:]
            num_rev = soup.find('span', {'class': 'rating__common-subtitle'})
            if num_rev:
                num_rev_str = num_rev.text
                count = re.findall(r'\d+', num_rev_str)[0]
            print(f'Сайт: {site_name}, Город: {city}, Название: {product_name}, Стоимость: {price}, '
                  f'Рейтинг: {rating}, Кол-во отзывов: {count}')
            update_rec(connection, id_db, product_name, price, rating, count)

        elif site == 2:

            town_selector = None
            try:
                town_selector = driver.find_element(By.XPATH, '//div[contains(@class, "TownSelector__chosen")]')
            except NoSuchElementException:
                pass
            if town_selector:
                strong = town_selector.find_element(By.TAG_NAME, 'strong')
                if strong:
                    site_city = strong.text
                    if site_city != city:
                        try:
                            lis = driver.find_elements(By.XPATH, '//li[contains(@class, "TownSelector-option")]')
                            for li in lis:
                                strong = li.find_element(By.TAG_NAME, 'strong')
                                city_strong = ''
                                if strong:
                                    city_strong = strong.text
                                if city in city_strong:
                                    strong.click()
                                    time.sleep(2)
                        except StaleElementReferenceException:
                            pass
            else:
                header_city = driver.find_element(By.XPATH, '//button[contains(@class, "HeaderCity")]')
                if header_city:
                    span = header_city.find_element(By.TAG_NAME, 'span')
                    if span:
                        site_city = span.text
                        if site_city != city:
                            try:
                                header_city.click()
                                time.sleep(2)
                                lis = driver.find_elements(By.XPATH,
                                                           '//li[contains(@class, "TownSelector-option")]')
                                for li in lis:
                                    strong = li.find_element(By.TAG_NAME, 'strong')
                                    city_strong = ''
                                    if strong:
                                        city_strong = strong.text
                                    if city in city_strong:
                                        strong.click()
                                        time.sleep(2)
                            except StaleElementReferenceException:
                                pass

            time.sleep(2)
            soup = get_soup(link_split[-2], driver.page_source)
            h1 = soup.find('h1')
            if h1:
                product_name = h1.text
            div = soup.find('div', class_='variantButton', attrs={'aria-selected': 'true'})
            if div:
                span_price = div.find('span', {'class': 'moneyprice__content'})
                if span_price:
                    price = span_price.text
                div_raring = div.find('div', {'class': 'variantButton__rating'})
                if div_raring:
                    span_rating = div_raring.find('span', {'class': 'ItemRating__label'})
                    if span_rating:
                        rating = span_rating.text
                    small = div_raring.find('small')
                    if small:
                        count = small.text
                        count = re.findall(r'\d+', count)[0]

            print(f'Сайт: {site_name}, Город: {city}, Название: {product_name}, Стоимость: {price},'
                  f' Рейтинг: {rating}, Кол-во отзывов: {count}')
            update_rec(connection, id_db, product_name, price, rating, count)

        elif site == 3:

            driver = get_selenium_driver(False, True)
            driver.get(link)
            active_city = driver.find_element(By.XPATH, '//span[contains(@class, "active-city")]')
            if active_city:
                site_city = active_city.text
                if site_city != city:
                    head_row_city = driver.find_element(By.XPATH, '//div[contains(@class, "m-header-top-row__city")]')
                    if head_row_city:
                        head_row_city.click()
                        time.sleep(1)
                        try:
                            modal = driver.find_element(By.ID, 'modal')
                            if modal:
                                cities = modal.find_elements(By.XPATH, '//a[contains(@data-action, "changeCity")]')
                                for city_a in cities:
                                    gorod = city_a.text
                                    if gorod == city:
                                        city_a.click()
                                        time.sleep(1)
                        except StaleElementReferenceException:
                            pass
                time.sleep(1)
                driver.refresh()
                soup = get_soup(link_split[-1], driver.page_source)
                h1 = soup.find('h1')
                if h1:
                    product_name = soup.find('h1').text
                price_div = soup.find('div', {'class': 'tnyXy7x _1nPhdxw'})
                if price_div:
                    price = price_div.text.split(' ')[1]
                print(f'Сайт: {site_name}, Город: {city}, Название: {product_name}, Стоимость: {price},'
                      f' Рейтинг: {rating}, Кол-во отзывов: {count}')
                update_rec(connection, id_db, product_name, price, rating, count)

        elif site == 4:

            WebDriverWait(driver, 60).until(
                expected_conditions.presence_of_element_located(
                    (By.CLASS_NAME, "header-top-container-changer")
                ))
            try:
                cook_but = driver.find_element(By.CLASS_NAME, 'cookie-accept-button')
                if cook_but:
                    cook_but.click()
            except NoSuchElementException:
                pass
            city_title = driver.find_element(By.XPATH, "//span[contains(@class,'city-title ml-2')]")
            if city_title:
                site_city = city_title.text
                if site_city != city:
                    select_city = driver.find_element(By.XPATH, f"//a[contains(@data-location-code,'{lat_city}')]")
                    if select_city is None:
                        print(f'Сайт: {site_name}, Город: {city}, Название: {product_name}, Стоимость: {price},'
                              f' Рейтинг: {rating}, Кол-во отзывов: {count}')
                        update_rec(connection, id_db, product_name, price, rating, count)
                    else:
                        driver.execute_script("arguments[0].click();", select_city)
                        time.sleep(1)
                soup = get_soup(link_split[4], driver.page_source)
                h1 = soup.find('h1')
                if h1:
                    product_name = h1.text
                price_div = soup.find('div', {'class': 'item-prop item-price my-3'})
                if price_div:
                    current_price = price_div.find('div', {'class': 'catalog-item-price-current'})
                    if current_price:
                        price = current_price.find('span', {'class': 'price'})
                        if price:
                            price = price.text[:-2].replace(' ', '')
                            price = price.replace(',', '.')

                print(f'Сайт: {site_name}, Город: {city}, Название: {product_name}, Стоимость: {price},'
                      f' Рейтинг: {rating}, Кол-во отзывов: {count}')
                update_rec(connection, id_db, product_name, price, rating, count)

        elif site == 5:

            dialog = None
            try:
                dialog = driver.find_element(By.XPATH, '//div[contains(@role, "dialog")]')
            except NoSuchElementException:
                time.sleep(1)
                pass

            try:
                if dialog is None:
                    dialog = driver.find_element(By.XPATH, '//div[contains(@role, "dialog")]')
            except NoSuchElementException:
                pass

            if dialog:
                conf_city_mod = dialog.find_element(By.XPATH, '//div[contains(@class, "confirmation-city-modal")]')
                if conf_city_mod:
                    conf_city = conf_city_mod.text
                    conf_city_spl = conf_city.split('?')
                    conf_spl = conf_city_spl[0].split('город')
                    city_confirm = conf_spl[1][1:]
                    if city_confirm in city:
                        but_yes = dialog.find_element(By.XPATH, '//button[contains(@class, "button--red city-btn")]')
                        if but_yes:
                            but_yes.click()
                            time.sleep(1)
                    else:
                        but_no = dialog.find_element(By.XPATH, '//button[contains(@class, "cancel-btn")]')
                        but_no.click()
                        time.sleep(2)
                        choose_city_div = driver.find_element(By.XPATH, '//div[contains(@role, "dialog")]')
                        if choose_city_div:
                            time.sleep(1)
                            city_but = choose_city_div.find_element(By.XPATH, f'//button[text()="{city}"]')
                            if city_but:
                                city_but.click()
            else:

                button = driver.find_element(
                    By.XPATH,
                    '//button[@class="flex gap-2 items-center px-1 hover:text-color-primary text-14"]')
                if button:
                    site_city = button.get_attribute('innerText').replace(' ', '')
                    site_city = site_city.replace('\n', '')
                    if site_city != city:
                        driver.maximize_window()
                        driver.execute_script("arguments[0].click();", button)
                        city_popup = driver.find_element(By.XPATH, '//div[contains(@class, "city-popup shadow-base")]')
                        if city_popup:
                            but_no = city_popup.find_element(By.XPATH, '//button[contains(@class, "button--white")]')
                            but_no.click()
                            time.sleep(2)
                            choose_city_div = driver.find_element(By.XPATH, '//div[contains(@role, "dialog")]')
                            if choose_city_div:
                                time.sleep(1)
                                city_but = choose_city_div.find_element(By.XPATH, f'//button[text()="{city}"]')
                                if city_but:
                                    city_but.click()
                        driver.minimize_window()
            time.sleep(2)
            soup = get_soup(link_split[4], driver.page_source)
            h1 = soup.find('h1')
            if h1:
                product_name = h1.text

            product_top = soup.find('div', {'class': 'product-top__aside'})
            if product_top:
                price_div = soup.find('div', {'class': 'price-info__price'})
                if price_div:
                    price_info = soup.find('div', {'class': 'price-info'})
                    if price_info:
                        price_val = price_div.find('span', {'class': 'price-value'})
                        if price_val:
                            price = price_val.text[:-2].replace(' ', '')
            rating_span = soup.find('span', {'class': 'product-stars-value'})
            if rating_span:
                rating = rating_span.text
                rating = re.findall(r'\d+', rating)[0]
            count_span = soup.find('span', {'class': 'product-stars-label'})
            if count_span:
                count = count_span.text
                count = re.findall(r'\d+', count)[0]
            print(f'Сайт: {site_name}, Город: {city}, Название: {product_name}, Стоимость: {price},'
                  f' Рейтинг: {rating}, Кол-во отзывов: {count}')
            update_rec(connection, id_db, product_name, price, rating, count)

    except NoSuchElementException as ex:
        print(ex)
        reason = "Элемент не найден"
        secure.log.write_log(reason, ex)
        pass


def get_soup(file_name, page_content):
    with open(f'data/wrk/{file_name}.html', 'w') as file:
        file.write(page_content)
    with open(f"data/wrk/{file_name}.html", encoding="utf-8") as file:
        src = file.read()
    return BeautifulSoup(src, "lxml")
