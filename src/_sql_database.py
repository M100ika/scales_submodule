import sqlite3
import os
from datetime import datetime
import json
import requests
from loguru import logger
from _config_manager import ConfigManager


class SqlDatabase:
    def __init__(self, db_path=None):
        self.config_manager = ConfigManager()
        self.__url_median = self.config_manager.get_setting("Parameters", "median_url")
        self.__url_array = self.config_manager.get_setting("Parameters", "array_url")
        self.__headers = {'Content-type': 'application/json'}

        if db_path is None:
            script_dir = os.path.dirname(os.path.realpath(__file__))
            self.__sql_table_path = os.path.join(script_dir, 'sql_table.db')
        else:
            self.__sql_table_path = db_path

        self.__table_check()

    def no_internet(self, payload):
        """Автоматически определяет, в какую таблицу сохранить данные"""
        if not payload:
            logger.error('SqlDatabase no_internet: Empty payload')
            return

        if "AnimalNumber" in payload:
            table_name = "json_data_median"
        elif "ScalesSerialNumber" in payload:
            table_name = "json_data_array"
        else:
            logger.error('SqlDatabase no_internet: Unknown data format')
            return

        self.__insert_data(payload, table_name)

    def internet_on(self):
        """Проверить интернет и попытаться отправить сохраненные данные."""
        try:
            # Проверка наличия интернета перед отправкой
            requests.get("https://www.google.com", timeout=5)

            # Если интернет есть, пробуем отправить все накопленные данные
            self.__send_saved_data("json_data_median", self.__url_median)
            self.__send_saved_data("json_data_array", self.__url_array)
        except requests.RequestException:
            logger.warning('Internet is not available. Data will remain in the database.')

    def __table_check(self):
        """Создать таблицы, если не существует"""
        try:
            with sqlite3.connect(self.__sql_table_path) as db:
                sql = db.cursor()
                sql.execute("""
                    CREATE TABLE IF NOT EXISTS json_data_median (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        AnimalNumber TEXT,
                        Date TEXT,
                        Weight REAL,
                        ScalesModel TEXT
                    )""")
                sql.execute("""
                    CREATE TABLE IF NOT EXISTS json_data_array (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ScalesSerialNumber TEXT,
                        WeighingStart TEXT,
                        WeighingEnd TEXT,
                        RFIDNumber TEXT,
                        Data TEXT
                    )""")
                db.commit()
        except Exception as e:
            logger.error(f'SqlDatabase __table_check: {e}')

    def __insert_data(self, payload, table_name):
        """Сохранить данные в базу"""
        try:
            with sqlite3.connect(self.__sql_table_path) as db:
                sql = db.cursor()
                values = self.__table_values_convert(payload, table_name)
                if table_name == "json_data_median":
                    sql.execute(
                        """INSERT INTO json_data_median 
                           (AnimalNumber, Date, Weight, ScalesModel) 
                           VALUES (?, ?, ?, ?);""",
                        values
                    )
                elif table_name == "json_data_array":
                    sql.execute(
                        """INSERT INTO json_data_array 
                           (ScalesSerialNumber, WeighingStart, WeighingEnd, RFIDNumber, Data) 
                           VALUES (?, ?, ?, ?, ?);""",
                        values
                    )
                db.commit()
                logger.info(f"Data saved locally in {table_name}: {values}")
        except Exception as e:
            logger.error(f'SqlDatabase __insert_data: {e}')

    def __table_values_convert(self, payload, table_name):
        if table_name == "json_data_median":
            return (payload['AnimalNumber'], payload["Date"], payload["Weight"], payload["ScalesModel"])
        elif table_name == "json_data_array":
            return (payload['ScalesSerialNumber'], payload["WeighingStart"], payload["WeighingEnd"], payload["RFIDNumber"], json.dumps(payload["Data"]))

    def __db_row_to_json(self, db_row, table_name):
        if table_name == "json_data_median":
            return {
                "AnimalNumber": db_row[1],
                "Date": db_row[2],
                "Weight": db_row[3],
                "ScalesModel": db_row[4]
            }
        elif table_name == "json_data_array":
            return {
                "ScalesSerialNumber": db_row[1],
                "WeighingStart": db_row[2],
                "WeighingEnd": db_row[3],
                "RFIDNumber": db_row[4],
                "Data": json.loads(db_row[5])
            }

    def __take_all_data(self, table_name):
        try:
            with sqlite3.connect(self.__sql_table_path) as db:
                sql = db.cursor()
                sql.execute(f"SELECT * FROM {table_name}")
                return sql.fetchall()
        except Exception as e:
            logger.error(f'SqlDatabase __take_all_data: {e}')
            return []

    def __delete_saved_data(self, id, table_name):
        try:
            with sqlite3.connect(self.__sql_table_path) as db:
                sql = db.cursor()
                sql.execute(f"DELETE FROM {table_name} WHERE id = ?", (id,))
                db.commit()
        except Exception as e:
            logger.error(f'SqlDatabase __delete_saved_data: {e}')

    def __send_saved_data(self, table_name, url):
        """Отправить все сохранённые данные"""
        try:
            all_data = self.__take_all_data(table_name)
            for row in all_data:
                id = row[0]
                post_data = self.__db_row_to_json(row, table_name)
                response = requests.post(url, data=json.dumps(post_data), headers=self.__headers, timeout=5)
                if response.status_code == 200:
                    self.__delete_saved_data(id, table_name)
                    logger.info(f'Successfully sent data from {table_name}. ID: {id}')
                else:
                    logger.warning(f'Failed to send data from {table_name}. ID: {id}. Status code: {response.status_code}')
        except Exception as e:
            logger.error(f'SqlDatabase __send_saved_data: {e}')
