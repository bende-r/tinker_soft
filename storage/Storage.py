from abc import abstractmethod, ABC
from typing import List

from storage.Device import Device


class Storage(ABC):

    @abstractmethod
    def create_db(self):
        ...

    @abstractmethod
    def get_devices(self) -> List[Device]:
        ...

    @abstractmethod
    def add_device(self, mac: str) -> Device:
        ...

    @abstractmethod
    def get_device(self, mac: str) -> Device:
        ...

    @abstractmethod
    def update_device(self, device: Device) -> Device:
        ...

    @abstractmethod
    def update_online_device(self, device: Device, online: bool) -> Device:
        ...

    @abstractmethod
    def get_online_devices(self) -> List[Device]:
        ...

    @abstractmethod
    def delete_device(self, device: Device) -> bool:
        ...

    @abstractmethod
    def add_statistic_data(self, mac: str, temperature: float = 0,
                           humidity: float = 0, battery: float = 0):
        ...

    @abstractmethod
    def get_statistic_data(self, mac: str):
        ...
