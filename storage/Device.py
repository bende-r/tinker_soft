import json

class Device(object):
    def __init__(self, mac: str, avg_battery: float = 0.0,
                 avg_temperature: float = 0.0,
                 avg_humidity: float = 0.0,
                 is_online: bool = False):
        self._mac: str = mac
        self._avg_battery: float = avg_battery
        self._avg_temperature: float = avg_temperature
        self._avg_humidity: float = avg_humidity
        self._is_online: bool = is_online

    @property
    def mac(self):
        return self._mac

    @property
    def avg_battery(self):
        return self._avg_battery

    @avg_battery.setter
    def avg_battery(self, value):
        self._avg_battery = value

    @property
    def avg_temperature(self):
        return self._avg_temperature

    @property
    def avg_humidity(self):
        return self._avg_humidity

    @property
    def is_online(self):
        return self._is_online

    def __str__(self):
        return json.dumps(dict(self), ensure_ascii=False)

    def __iter__(self):
        yield from {
            "mac": self._mac,
            "avg_battery": self._avg_battery,
            "avg_temperature": self._avg_temperature,
            "avg_humidity": self._avg_humidity,
            "is_online": self.is_online
        }.items()

    @avg_temperature.setter
    def avg_temperature(self, value):
        self._avg_temperature = value

    @avg_humidity.setter
    def avg_humidity(self, value):
        self._avg_humidity = value

    @is_online.setter
    def is_online(self, value):
        self._is_online = value
