from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Union, List


class BaseSource(ABC):
    """Базовый абстрактный класс для работы с облачными хранилищами."""

    def __init__(self, token: str, source_type: Enum):
        """
        Инициализация базового класса.

        Args:
            token: Токен для авторизации
            source_type: Тип источника
        """
        self.token = token
        self.source_type = source_type
        self.client = None
        self.is_connected = False
        # self.is_async = False

    @abstractmethod
    def connect(self) -> bool:
        """Подключение к облачному хранилищу."""
        pass

    @abstractmethod
    def check_connection(self) -> bool:
        """Проверка подключения к облачному хранилищу."""
        pass

    @abstractmethod
    def list_directories(self, path: str = "/") -> List[str]:
        """Получение списка директорий."""
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_path: Union[str, Path]) -> bool:
        """Скачивание файла."""
        pass

    @abstractmethod
    def upload_file(self, local_path: Union[str, Path], remote_path: str) -> bool:
        """Загрузка файла."""
        pass

    @abstractmethod
    def search_directories(self, name: str, path: str = "/") -> List[str]:
        """Поиск директорий по имени."""
        pass

    def disconnect(self):
        """Отключение от облачного хранилища."""
        self.client = None
        self.is_connected = False
        pass
