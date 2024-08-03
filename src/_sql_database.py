import sqlite3
import os
from loguru import logger
import requests
import json
from _config_manager import ConfigManager


class SqlDatabase:
    def __init__(self):
        self.__config_manager = ConfigManager()
        self.__url = self.__config_manager.get_setting("Parameters", "url")
        self.__headers = {'Content-type': 'application/json'}
        self.__sql_table_path = '../feeder_log/sql_table.db'
        self.__table_check()


    def no_internet(self, payload):
        """Публичный метод для вызова, когда нет интернет-соединения."""
        if payload:
            self.__insert_data(payload)
        else:
            logger.error('SqlDatabase no_internet: Empty payload')


    def internet_on(self):
        """Публичный метод для вызова, когда интернет-соединение восстановлено."""
        try:
            with sqlite3.connect(self.__sql_table_path) as db:
                sql = db.cursor()
                count = sql.execute("SELECT COUNT(*) FROM json_data").fetchone()[0]
                if count > 0:
                    self.__send_saved_data()
        except Exception as e:
            logger.error(f'SqlDatabase internet_on: {e}')


    def __table_check(self):
        """Создает таблицу в базе данных, если она не существует."""
        try:
            with sqlite3.connect(self.__sql_table_path) as db:
                sql = db.cursor()
                sql.execute("""CREATE TABLE IF NOT EXISTS json_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Eventdatetime TEXT,
                    EquipmentType TEXT,
                    SerialNumber TEXT,
                    FeedingTime REAL,
                    RFIDNumber TEXT,
                    WeightLambda REAL,
                    FeedWeight REAL)""")
                db.commit()
        except Exception as e:
            logger.error(f'SqlDatabase __table_check: {e}')


    def __insert_data(self, payload):
        """Вставляет данные в таблицу."""
        try:
            with sqlite3.connect(self.__sql_table_path) as db:
                sql = db.cursor()
                values = self.__table_values_convert(payload)
                sql.execute("INSERT INTO json_data (Eventdatetime, EquipmentType, SerialNumber, FeedingTime, RFIDNumber, WeightLambda, FeedWeight) VALUES (?,?,?,?,?,?,?);", values)
                db.commit()
        except Exception as e:
            logger.error(f'SqlDatabase __insert_data: {e}')


    def __table_values_convert(self, payload):
        """Конвертирует JSON в кортеж значений."""
        try:
            return (payload['Eventdatetime'], payload["EquipmentType"], payload["SerialNumber"],
                    payload["FeedingTime"], payload["RFIDNumber"], payload["WeightLambda"], payload["FeedWeight"])
        except Exception as e:
            logger.error(f'SqlDatabase __table_values_convert: {e}')


    def __take_first_data(self):
        """Извлекает первую строку данных из таблицы."""
        try:
            with sqlite3.connect(self.__sql_table_path) as db:
                sql = db.cursor()
                sql.execute("SELECT * FROM json_data ORDER BY id LIMIT 1")
                return sql.fetchone()
        except Exception as e:
            logger.error(f'SqlDatabase __take_first_data: {e}')
            return None


    def __delete_saved_data(self, id):
        """Удаляет данные из таблицы по идентификатору."""
        try:
            with sqlite3.connect(self.__sql_table_path) as db:
                sql = db.cursor()
                sql.execute("DELETE from json_data WHERE id = ?", (id,))
                db.commit()
        except Exception as e:
            logger.error(f'SqlDatabase __delete_saved_data: {e}')


    def __send_saved_data(self):
        """Отправляет сохраненные данные на сервер."""
        try:
            data = self.__take_first_data()
            if data:
                id, post_data = data[0], self.__table_values_convert(data[1:])
                response = requests.post(self.__url, data=json.dumps(post_data), headers=self.__headers, timeout=5)
                response.raise_for_status()
                self.__delete_saved_data(id)
        except Exception as e:
            logger.error(f'SqlDatabase __send_saved_data: {e}')
