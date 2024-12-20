from datetime import datetime, timedelta
import logging
from threading import Lock
from btlewrap.base import BluetoothInterface, BluetoothBackendException

_HANDLE_READ_BATTERY_LEVEL = 0x0018
_HANDLE_READ_FIRMWARE_VERSION = 0x0024
_HANDLE_READ_NAME = 0x03
_HANDLE_READ_WRITE_SENSOR_DATA = 0x0010

MI_TEMPERATURE = "temperature"
MI_HUMIDITY = "humidity"
MI_BATTERY = "battery"

_LOGGER = logging.getLogger(__name__)

class SensorDataPoller(object):
    def __init__(self, mac, backend, cache_timeout=10, retries=1, adapter='hci0', ble_timeout=10):
        self._mac = mac
        self._bt_interface = BluetoothInterface(backend, adapter=adapter)
        self._cache = None
        self._cache_timeout = timedelta(seconds=cache_timeout)
        self._last_read = None
        self._fw_last_read = None
        self.retries = retries
        self.ble_timeout = ble_timeout
        self.lock = Lock()
        self._firmware_version = None
        self.battery = None

    def name(self):
        with self._bt_interface.connect(self._mac) as connection:
            name = connection.read_handle(_HANDLE_READ_NAME)  

        if not name:
            raise BluetoothBackendException("Could not read NAME using handle %s"
                                            " from Mi Temp sensor %s" % (hex(_HANDLE_READ_NAME), self._mac))
        return ''.join(chr(n) for n in name)

    def fill_cache(self):
        _LOGGER.debug('Filling cache with new sensor data.')
        try:
            self.firmware_version()
        except BluetoothBackendException:
            self._last_read = datetime.now() - self._cache_timeout + \
                timedelta(seconds=20)
            raise

        with self._bt_interface.connect(self._mac) as connection:
            try:
                connection.wait_for_notification(_HANDLE_READ_WRITE_SENSOR_DATA, self, self.ble_timeout)
            except BluetoothBackendException:
                self._last_read = datetime.now() - self._cache_timeout + \
                    timedelta(seconds=20)
                return

    def battery_level(self):
        self.firmware_version()
        return self.battery

    def firmware_version(self):
        if (self._firmware_version is None) or \
                (datetime.now() - timedelta(hours=24) > self._fw_last_read):
            self._fw_last_read = datetime.now()
            with self._bt_interface.connect(self._mac) as connection:
                res_firmware = connection.read_handle(_HANDLE_READ_FIRMWARE_VERSION)  # pylint: disable=no-member
                _LOGGER.debug('Received result for handle %s: %s',
                              _HANDLE_READ_FIRMWARE_VERSION, res_firmware)
                res_battery = connection.read_handle(_HANDLE_READ_BATTERY_LEVEL)  # pylint: disable=no-member
                _LOGGER.debug('Received result for handle %s: %d',
                              _HANDLE_READ_BATTERY_LEVEL, res_battery)

            if res_firmware is None:
                self._firmware_version = None
            else:
                self._firmware_version = res_firmware.decode("utf-8")

            if res_battery is None:
                self.battery = 0
            else:
                self.battery = int(ord(res_battery))
        return self._firmware_version

    def parameter_value(self, parameter, read_cached=True):
        if parameter == MI_BATTERY:
            return self.battery_level()

        with self.lock:
            if (read_cached is False) or \
                    (self._last_read is None) or \
                    (datetime.now() - self._cache_timeout > self._last_read):
                self.fill_cache()
            else:
                _LOGGER.debug("Using cache (%s < %s)",
                              datetime.now() - self._last_read,
                              self._cache_timeout)

        if self.cache_available():
            return self._parse_data()[parameter]
        else:
            raise BluetoothBackendException("Could not read data from Mi Temp sensor %s" % self._mac)

    def _check_data(self):
        if not self.cache_available():
            return

        parsed = self._parse_data()
        _LOGGER.debug('Received new data from sensor: Temp=%.1f, Humidity=%.1f',
                      parsed[MI_TEMPERATURE], parsed[MI_HUMIDITY])

        if parsed[MI_HUMIDITY] > 100:  # humidity over 100 procent
            self.clear_cache()
            return

        if parsed[MI_TEMPERATURE] == 0:  # humidity over 100 procent
            self.clear_cache()
            return

    def clear_cache(self):
        self._cache = None
        self._last_read = None

    def cache_available(self):
        return self._cache is not None

    def _parse_data(self):
        data = self._cache

        res = dict()
        for dataitem in data.strip('\0').split(' '):
            dataparts = dataitem.split('=')
            if dataparts[0] == 'T':
                res[MI_TEMPERATURE] = float(dataparts[1])
            elif dataparts[0] == 'H':
                res[MI_HUMIDITY] = float(dataparts[1])
        return res

    @staticmethod
    def _format_bytes(raw_data):
        """Prettyprint a byte array."""
        if raw_data is None:
            return 'None'
        return ' '.join([format(c, "02x") for c in raw_data]).upper()

    def handleNotification(self, handle, raw_data):  
        if raw_data is None:
            return
        data = raw_data.decode("utf-8").strip(' \n\t')
        self._cache = data
        self._check_data()
        if self.cache_available():
            self._last_read = datetime.now()
        else:
            # If a sensor doesn't work, wait 5 minutes before retrying
            self._last_read = datetime.now() - self._cache_timeout + \
                timedelta(seconds=20)
