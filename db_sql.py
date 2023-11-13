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
                    url varchar(250) NOT NULL,
                    city varchar(35) NOT NULL,
                    product_name varchar(250),
                    price varchar(20),
                    rating varchar(5),
                    count varchar(5),
                    site_name varchar(250) NOT NULL,
                    file_name varchar(100) NOT NULL,
                    UNIQUE (url, file_name),
                    CONSTRAINT "ads_pk" PRIMARY KEY ("id", "url")
                    ) WITH (
                    OIDS=FALSE
                );"""
            )

            print("[INFO] Table pharm created successfully")
    except Exception as _ex:
        log.write_log("create_table ", _ex)
        print("Error while working with PostgreSQL, create_table ", _ex)


def update_rec(connection, id_db, product_name, price, rating, count):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""UPDATE pharm SET product_name = '{product_name}', price = '{price}', 
                rating = '{rating}', count = '{count}' WHERE id = {id_db};"""
            )

    except Exception as _ex:
        log.write_log("update_rec:", _ex)
        print("Error while working with PostgreSQL, update_rec: ", _ex)


def insert_main_data(connection, url, city, site_name, file_name):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""INSERT INTO pharm (url, city, site_name, file_name) VALUES 
                    ('{url}', '{city}', '{site_name}', '{file_name}');"""
            )
    except Exception as _ex:
        log.write_log("insert_main_data: ", _ex)
        print("Error while working with PostgreSQL, insert_main_data: ", _ex)


def get_result(files):
    connection = None
    try:
        connection = connect_db()
        with connection.cursor() as cursor:
            for file in files:
                file_name = file[:-4]
                sql = f"""SELECT * FROM pharm WHERE file_name = '{file_name}';"""
                cursor.execute(sql)
                rows = cursor.fetchall()
                dt = datetime.now()
                file_name = dt.strftime('%Y-%m-%d')
                with open(f"result/{file_name}.csv", "a", newline='', encoding="utf-8") as f:
                    writer = csv.writer(f, delimiter='\t')
                    writer.writerows(rows)
    except Exception as _ex:
        log.write_log("get_result", _ex)
        print("Error while working with PostgreSQL, get_result ", _ex)
    finally:
        if connection:
            connection.close()
            print("[INFO] Данные выгружены в CSV файл")


def check_url_in_bd(connection, url, csv_name):
    with connection.cursor() as cursor:
        cursor.execute(f"""SELECT id FROM pharm WHERE url = '{url}' AND file_name = '{csv_name}';""")
        return cursor.fetchone() is not None


def delete_data_from_table(files):
    connection = None
    try:
        connection = connect_db()
        connection.autocommit = True
        with connection.cursor() as cursor:
            for file in files:
                file_name = file[:-4]
                cursor.execute(f"""DELETE FROM pharm WHERE file_name = '{file_name}';""")
                print(f"[INFO] Data by filename: {file_name} was deleted")
    except Exception as _ex:
        log.write_log("delete_data_from_table ", _ex)
        print("Error while working with PostgreSQL, delete_table ", _ex)
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
            cursor.execute(f"""DROP TABLE IF EXISTS pharm;""")
            print("[INFO] TABLE pharm was deleted")
    except Exception as _ex:
        log.write_log("delete_table ", _ex)
        print("Error while working with PostgreSQL, delete_table ", _ex)
    finally:
        if connection:
            connection.close()
            print("[INFO] PostgreSQL connection closed")


def get_main_data(connection, file_name):
    with connection.cursor() as cursor:
        cursor.execute(f"""SELECT id, url, city, site_name FROM pharm WHERE file_name = '{file_name}' 
        ORDER BY site_name;""")
        if cursor.fetchone is not None:
            return cursor.fetchall()
