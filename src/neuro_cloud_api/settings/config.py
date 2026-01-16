from dataclasses import dataclass
from enum import Enum


# Класс-Конфиг для того, чтобы параметры хранились в нем
@dataclass
class NeuroCloudApiConfig:
    '''
    Configuration for NeuroCloudApi
    token: str - Токен для подключению Облачного сервиса
    source_type: Enum - Тип сервиса (YANDEX_DISK | GOOGLE_DRIVE | S3)
    home_folder: str - Корневая папка, по-умолчанию, например, MATLLER
    '''
    token: str
    source_type: Enum
    home_folder: str
    async_enabled: bool = True
