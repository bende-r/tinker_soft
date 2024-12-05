import threading
import time

from btlewrap.bluepy import BluepyBackend
from bluepy.btle import BTLEException
from typing import List
from bluepy.btle import Scanner

from sensor_data_poller.SensorDataPoller import SensorDataPoller
from sensor_data_poller.SensorDataPoller import MI_TEMPERATURE, MI_HUMIDITY, MI_BATTERY

from sensor_scanner.SensorScanner import SensorScanner
from storage.Sensor import Sensor
from storage.SQLiteStorage import SQLiteStorage
from storage.Storage import Storage
from logger.logger import get_logger

logger = get_logger(__name__)
MAC_START = '4C:65:A8:'.lower()

class SensorManager(object):
    def __init__(self, storage: Storage = SQLiteStorage(), timeout: int = 5):
        self._pollers = list()
        self._storage: Storage = storage
        self._timeout = timeout
        self._scanner = Scanner().withDelegate(SensorScanner())
        thr = threading.Thread(target=self._collect_statistic_data, daemon=True, name='update_devices_data')
        thr.start()

    @property
    def storage(self):
        return self._storage

    def _collect_statistic_data(self, timeout=10):
        logger.info(f"Start thread update devices data")
        while True:
            for d in self._storage.get_devices():
                self.update_device_info(d)
                self._storage.update_device(d)
            time.sleep(timeout)

    def update_device_info(self, device: Sensor):
        poller = SensorDataPoller(device.mac, BluepyBackend, ble_timeout=self._timeout)
        try:
            temperature = poller.parameter_value(MI_TEMPERATURE)
            humidity = poller.parameter_value(MI_HUMIDITY)
            battery = poller.parameter_value(MI_BATTERY)
            logger.info(f"Statistic data from device "
                         f"{device.mac} - temperature {temperature} - humidity {humidity} - battery {battery}")
            self._storage.add_statistic_data(device.mac, temperature, humidity, battery)
            stat_data = self._get_stat(device)
            avg_temperature = 0
            avg_humidity = 0
            avg_battery = 0
            for d in stat_data:
                avg_temperature = d[3]
                avg_humidity = d[4]
                avg_battery = d[5]
            device.avg_temperature = avg_temperature #/ len(stat_data)
            device.avg_humidity = avg_humidity #/ len(stat_data)
            device.avg_battery = avg_battery #/ len(stat_data)
            device.is_online = True
            self._storage.update_device(device)
        except BTLEException as e:
            logger.error(f"Error connecting to device {device.mac}: {str(e)}")
            self._storage.update_online_device(device, False)
        except Exception as e:
            logger.error(f"Error polling device {device.mac}. Device might be unreachable or offline.")
            self._storage.update_online_device(device, False)
        finally:
            ...

    def scan_devices(self) -> List:
        logger.info(f"Start scan devices ...")
        devices = list()
        try:
            scan_dev = self._scanner.scan(passive=True, timeout = self._timeout)
    
            for d in scan_dev:
                logger.info(f"Device {d.addr} ({d.addrType}), RSSI={d.rssi}")
                logger.info(f"Device found - mac: {d.addr}, type: {d.addrType}, RSSI: {d.rssi}")
                if d.addr.startswith(MAC_START):
                    devices.append({"mac": d.addr, "type": d.addrType, "RSSI": d.rssi})
            logger.info(f" {len(devices)} devices found")
        except Exception as e:
            logger.error(f"Error while scan devices: {str(e)} ")

        return devices

    def add_device(self, mac) -> Sensor:
        return self._storage.add_device(mac)

    def get_devices(self) -> List:
        return self._storage.get_devices()

    def get_online_devices(self) -> List:
        return self._storage.get_online_devices()

    def get_device(self, mac) -> Sensor:
        return self._storage.get_device(mac)

    def _get_stat(self, device: Sensor) -> List:
        return self._storage.get_statistic_data(device.mac)

    def delete_device(self, device: Sensor):
        return self._storage.delete_device(device)
