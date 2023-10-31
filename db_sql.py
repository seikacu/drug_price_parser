import csv

import psycopg

from datetime import datetime

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
        cursor.execute("select exists(select * from information_schema.tables where table_name=%s)", ('pharm',))
        return cursor.fetchone()[0]


def create_table(connection):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """CREATE TABLE pharm (
                    id serial NOT NULL,
                    url varchar(250) NOT NULL UNIQUE,
                    city varchar(35) NOT NULL,
                    product_name varchar(100),
                    price varchar(20),
                    rating varchar(5),
                    count varchar(5),
                    site_name varchar(250) NOT NULL,
                    file_name varchar(100) NOT NULL,
                    CONSTRAINT "ads_pk" PRIMARY KEY ("id","url")
                    ) WITH (
                    OIDS=FALSE
                );"""
            )

            print("[INFO] Table created successfully")
    except Exception as _ex:
        log.write_log("create_table ", _ex)
        print("Error while working with PostgreSQL", _ex)


def insert_to_table(connection, url, city, product_name, price, rating, count,
                    site_name, file_name):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""INSERT INTO pharm (url, city, product_name, price, rating, count,
                site_name, file_name) VALUES 
                    ('{url}', '{city}', '{product_name}', '{price}', '{rating}',
                    '{count}', '{site_name}', '{file_name}');"""
            )

    except Exception as _ex:
        log.write_log("insert_to_table ", _ex)
        print("Error while working with PostgreSQL", _ex)


# def add_phone1(connection, id_db, phone):
#     try:
#         with connection.cursor() as cursor:
#             cursor.execute(f"""UPDATE ads SET phone_1 = '{phone}' WHERE id = {id_db};""")
#
#             print(f"[INFO] Phone_1 {phone} was successfully add")
#
#     except Exception as _ex:
#         log.write_log("add_phone1 ", _ex)
#         print("Error while working with PostgreSQL", _ex)


def get_result(csv_name):
    connection = None
    try:
        connection = connect_db()
        with connection.cursor() as cursor:
            sql = f"""SELECT * FROM pharm WHERE file_name = '{csv_name}';"""
            cursor.execute(sql)
            rows = cursor.fetchall()
            dt = datetime.now()
            file_name = dt.strftime('%Y-%m-%d')
            with open(f"result/{file_name}.csv", "a", newline='', encoding="utf-8") as file:
                writer = csv.writer(file, delimiter='\t')
                writer.writerows(rows)
    except Exception as _ex:
        log.write_log("get_result", _ex)
        print("Error while working with PostgreSQL", _ex)
    finally:
        if connection:
            connection.close()
            print("[INFO] Данные выгружены в CSV файл")


def check_url_in_bd(connection, url):
    with connection.cursor() as cursor:
        cursor.execute(f"""SELECT url FROM pharm WHERE url = '{url}';""")
        return cursor.fetchone() is not None


# def delete_data_from_table(file_name):
#     connection = None
#     try:
#         connection = connect_db()
#         connection.autocommit = True
#         with connection.cursor() as cursor:
#             cursor.execute(f"""DELETE FROM pharm WHERE file_name = '{file_name}';""")
#             print("[INFO] Data was deleted")
#     except Exception as _ex:
#         log.write_log("delete_data_from_table ", _ex)
#         print("Error while working with PostgreSQL", _ex)
#     finally:
#         if connection:
#             connection.close()
#             print("[INFO] PostgreSQL connection closed")


# def delete_table():
#     connection = None
#     try:
#         connection = connect_db()
#         connection.autocommit = True
#         with connection.cursor() as cursor:
#             cursor.execute(f"""DROP TABLE IF EXISTS pharm;""")
#             print("[INFO] TABLE was deleted")
#     except Exception as _ex:
#         log.write_log("delete_table ", _ex)
#         print("Error while working with PostgreSQL", _ex)
#     finally:
#         if connection:
#             connection.close()
#             print("[INFO] PostgreSQL connection closed")

# def get_data_from_table(connection, category_name):
#     with connection.cursor() as cursor:
#         cursor.execute(f"""SELECT id, url FROM ads WHERE launch_point = '{category_name}'
#         AND phone_1 IS NULL;""")
#         if cursor.fetchone is not None:
#             return cursor.fetchall()
