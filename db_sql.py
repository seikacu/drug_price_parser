import csv

import psycopg

from secure import PSql, log


def connect_db():
    connection = psycopg.connect(
        host=PSql.host,
        user=PSql.user,
        password=PSql.password,
        dbname=PSql.db_name
    )
    return connection



def check_exist_table(connection):
    with connection.cursor() as cursor:
        cursor.execute("select exists(select * from information_schema.tables where table_name=%s)", ('ads',))
        return cursor.fetchone()[0]


def create_table_ads(connection):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """CREATE TABLE ads (
                    id serial NOT NULL,
                    url varchar(200) NOT NULL UNIQUE,
                    category varchar(50) NOT NULL,
                    sub_category_1 varchar(100),
                    sub_category_2 varchar(100),
                    sub_category_3 varchar(100),
                    sub_category_4 varchar(100),
                    sub_category_5 varchar(100),
                    location varchar(50) NOT NULL,
                    phone_1 varchar(20),
                    phone_2 varchar(20),
                    launch_point varchar(50) NOT NULL,
                    CONSTRAINT "ads_pk" PRIMARY KEY ("id","url")
                    ) WITH (
                    OIDS=FALSE
                );"""
            )

            print("[INFO] Table created successfully")

    except Exception as _ex:
        log.write_log("create_table_ads ", _ex)
        print("Error while working with PostgreSQL", _ex)


def insert_to_table(connection, url, category, sub_category_1, sub_category_2, sub_category_3, sub_category_4,
                    sub_category_5, location, launch_point):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""INSERT INTO ads (url, category, sub_category_1, sub_category_2, sub_category_3, sub_category_4,
                sub_category_5, location, launch_point) VALUES 
                    ('{url}', '{category}', '{sub_category_1}', '{sub_category_2}', '{sub_category_3}',
                    '{sub_category_4}', '{sub_category_5}', '{location}', '{launch_point}');"""
            )

    except Exception as _ex:
        log.write_log("insert_to_table ", _ex)
        print("Error while working with PostgreSQL", _ex)


def add_phone1(connection, id_db, phone):
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""UPDATE ads SET phone_1 = '{phone}' WHERE id = {id_db};""")

            print(f"[INFO] Phone_1 {phone} was successfully add")

    except Exception as _ex:
        log.write_log("add_phone1 ", _ex)
        print("Error while working with PostgreSQL", _ex)


def add_phone2(connection, id_db, phone):
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""UPDATE ads SET phone_2 = '{phone}' WHERE id = {id_db};""")

            print(f"[INFO] Phone_2 {phone} was successfully add")

    except Exception as _ex:
        log.write_log("add_phone2 ", _ex)
        print("Error while working with PostgreSQL", _ex)


def get_data_to_csv_file(name_csv):
    connection = None
    split_name_csv = name_csv.split("_")
    try:
        connection = connect_db()
        with connection.cursor() as cursor:
            sql = f"""SELECT * FROM ads WHERE launch_point = '{split_name_csv[0]}'"""
            cursor.execute(sql)
            rows = cursor.fetchall()
            with open(f"result/{name_csv}.csv", "a", newline='', encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerows(rows)
    except Exception as _ex:
        log.write_log("get_data_to_csv_file ", _ex)
        print("Error while working with PostgreSQL", _ex)
    finally:
        if connection:
            connection.close()
            print("[INFO] Данные выгружены в CSV файл")


def check_url_in_bd(connection, url):
    with connection.cursor() as cursor:
        cursor.execute(f"""SELECT url FROM ads WHERE url = '{url}';""")
        return cursor.fetchone() is not None


def delete_data_from_table(category_name):
    connection = None
    try:
        connection = connect_db()
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(f"""DELETE FROM ads WHERE launch_point = '{category_name}';""")
            print("[INFO] Data was deleted")
    except Exception as _ex:
        log.write_log("delete_data_from_table ", _ex)
        print("Error while working with PostgreSQL", _ex)
    finally:
        if connection:
            connection.close()
            print("[INFO] PostgreSQL connection closed")


def delete_table():
    connection = None
    try:
        connection = connect_db()
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(f"""DROP TABLE IF EXISTS ads;""")
            print("[INFO] TABLE was deleted")
    except Exception as _ex:
        log.write_log("delete_table ", _ex)
        print("Error while working with PostgreSQL", _ex)
    finally:
        if connection:
            connection.close()
            print("[INFO] PostgreSQL connection closed")


def get_data_from_table(connection, category_name):
    with connection.cursor() as cursor:
        cursor.execute(f"""SELECT id, url FROM ads WHERE launch_point = '{category_name}'
        AND phone_1 IS NULL;""")
        if cursor.fetchone is not None:
            return cursor.fetchall()
