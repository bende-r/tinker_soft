from abc import abstractmethod, ABC
from typing import List

from storage.Sensor import Sensor

class Storage(ABC):

    @abstractmethod
    def create_db(self):
        ...

    @abstractmethod
    def get_devices(self) -> List[Sensor]:
        ...

    @abstractmethod
    def add_device(self, mac: str) -> Sensor:
        ...

    @abstractmethod
    def get_device(self, mac: str) -> Sensor:
        ...

    @abstractmethod
    def update_device(self, device: Sensor) -> Sensor:
        ...

    @abstractmethod
    def update_online_device(self, device: Sensor, online: bool) -> Sensor:
        ...

    @abstractmethod
    def get_online_devices(self) -> List[Sensor]:
        ...

    @abstractmethod
    def delete_device(self, device: Sensor) -> bool:
        ...

    @abstractmethod
    def add_statistic_data(self, mac: str, temperature: float = 0,
                           humidity: float = 0, battery: float = 0):
        ...

    @abstractmethod
    def get_statistic_data(self, mac: str):
        ...