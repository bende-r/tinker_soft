import os
import sqlite3 as sl
import datetime
from typing import List

from logger.logger import get_logger
from storage.Sensor import Sensor
from storage.Storage import Storage
from typing import Union

logger = get_logger(__name__)

def con_db(func):
    def wrapper(*args, **kwargs):
        con = None
        db = args[0].db
        try:
            con = sl.connect(db)
            #logger.info(f"Connection created: {con}")
            #logger.info("Connect to " + db)
            value = func(*args, **kwargs, connection=con)
            return value
        except sl.Error as e:
            if con:
                con.rollback()
            logger.error(f"Error during query: {str(e)}")
        except Exception as e:
            logger.error(f"Error connecting to database {db}: {str(e)}")
            return e
        finally:
            if con:
                #logger.info("Close connect to " + db)
                con.close()

    return wrapper

class SQLiteStorage(Storage):

    def __init__(self, db: str = 'devices.db'):
        self._db = db
        if self._db not in os.listdir():
            self.create_db()

    @property
    def db(self) -> str:
        return self._db

    @con_db
    def create_db(self, connection=None):
        cursor = connection.cursor()
        cursor.execute(''' create table 'devices' ( mac text not null unique unique, avg_battery REAL default 0,
                avg_temp REAL default 0, avg_humidity REAL default 0, online INTEGER default 0 not null);''')

        cursor.execute('''create table statistic_data ( id integer not null primary key autoincrement unique,
               divice_mac TEXT not null constraint statistic_data_devices_mac_fk references devices (mac), time TEXT not null,
              temperature REAL not null, humidity real not null, battery REAL not null);''')
        connection.commit()

    @con_db
    def get_devices(self, connection=None) -> List[Sensor]:
        devices = []
        cursor = connection.cursor()
        data = cursor.execute("SELECT * FROM 'devices'")
        for row in data:
            devices.append(Sensor(*row))
        return devices

    @con_db
    def get_device(self, mac: str, connection=None) -> Sensor:
        cursor = connection.cursor()
        data = cursor.execute(f"SELECT * FROM 'devices' WHERE mac = '{mac}'")
        for row in data:
            return Sensor(*row)

    @con_db
    def add_device(self, mac: str, connection=None) -> Union[Exception, Sensor, None]:
        cursor = connection.cursor()
        cursor.execute(f"INSERT INTO 'devices' (mac) VALUES ('{mac}')")
        connection.commit()
        if cursor.rowcount > 0:
            logger.info(f"Adding device {mac} success")
            return self.get_device(mac)
        else:
            logger.info(f"Adding device {mac} fail")
            return None

    @con_db
    def update_device(self, device: Sensor, connection=None) -> Sensor:
        
        logger.info(f"Received connection: {connection}") 
        print(f"Received connection: {connection}")  # Отобразить connection
        logger.info(f"Connection type: {type(connection)}")  # Тип объекта
        logger.info(f"Connection dir: {dir(connection)}")    # Список методов и атрибутов объекта

        cursor = connection.cursor()
        cursor.execute(f"UPDATE 'devices' SET avg_battery = {device.avg_battery}, avg_temp = {device.avg_temperature},"
                       f" avg_humidity = {device.avg_humidity}, online = {int(device.is_online)}"
                       f" WHERE mac = '{device.mac}'")
        connection.commit()
        logger.info(f"Updating device {device.mac} success")
        return device

    @con_db
    def update_online_device(self, device: Sensor, connection=None) -> Sensor:
        cursor = connection.cursor()
        cursor.execute(f"UPDATE 'devices' SET online = {int(device.is_online)} WHERE mac = '{device.mac}'")
        connection.commit()
        return device

    @con_db
    def get_online_devices(self, connection=None) -> List[Sensor]:
        devices = []
        cursor = connection.cursor()
        data = cursor.execute("SELECT * FROM 'devices' where online = 1")
        for row in data:
            devices.append(Sensor(*row))
        return devices

    @con_db
    def delete_device(self, device: Sensor, connection=None) -> bool:
        cursor = connection.cursor()
        cursor.execute(f"DELETE from 'devices' WHERE mac = '{device.mac}'")
        connection.commit()
        if cursor.rowcount > 0:
            logger.info(f"Deleting device {device.mac} success")
            return True
        else:
            logger.info(f"Deleting device {device.mac} fail")
            return False

    @con_db
    def add_statistic_data(self, mac: str, temperature: float = 0,
                           humidity: float = 0, battery: float = 0, connection=None):
        cursor = connection.cursor()
        cursor.execute(
            f"INSERT INTO 'statistic_data' (divice_mac, time, temperature, humidity, battery)"
            f" VALUES ('{mac}', '{datetime.datetime.now()}', {temperature}, {humidity}, {battery})")
        connection.commit()

    # @con_db
    # def get_statistic_data(self, mac: str, connection=None):
    #     statistic_data = []
    #     cursor = connection.cursor()
    #     data = cursor.execute(f"SELECT * FROM 'statistic_data' where divice_mac = '{mac}' and"
    #                           f" time like '{datetime.datetime.now().date()}%'")
    #     for row in data:
    #         statistic_data.append(row)
    #     return statistic_data

    @con_db
    def get_statistic_data(self, mac: str, start_date: str = None, end_date: str = None, connection=None):
        """
        Получить статистические данные за определённый период.

        :param mac: MAC-адрес устройства
        :param start_date: Начальная дата в формате 'YYYY-MM-DD'. По умолчанию None.
        :param end_date: Конечная дата в формате 'YYYY-MM-DD'. По умолчанию None.
        :param connection: SQLite соединение
        :return: Список записей статистики
        """
        statistic_data = []
        cursor = connection.cursor()

        # Базовый запрос
        query = f"SELECT * FROM 'statistic_data' WHERE divice_mac = '{mac}'"

        # Условия фильтрации по датам
        if start_date and end_date:
            query += f" AND time BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'"
        elif start_date:
            query += f" AND time >= '{start_date} 00:00:00'"
        elif end_date:
            query += f" AND time <= '{end_date} 23:59:59'"

        # Выполнение запроса
        logger.info(f"Executing query: {query}")
        data = cursor.execute(query)

        for row in data:
            statistic_data.append(row)
        return statistic_data

