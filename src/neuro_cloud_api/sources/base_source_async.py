from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, List, Any, Optional

from .source_type import SourceType


class BaseSourceAsync(ABC):
    """Базовый абстрактный класс для асинхронной работы с облачными хранилищами."""

    def __init__(self, token: str, source_type: SourceType):
        """
        Инициализация базового класса.

        Args:
            token: Токен для авторизации
            source_type: Тип источника
        """
        self._token = token
        self._source_type = source_type
        self._client: Optional[Any] = None
        self._is_connected = False

    @property
    def token(self) -> str:
        """Токен для авторизации."""
        return self._token

    @property
    def source_type(self) -> SourceType:
        """Тип источника."""
        return self._source_type

    @property
    def is_connected(self) -> bool:
        """Статус подключения."""
        return self._is_connected

    @abstractmethod
    async def connect(self) -> bool:
        """Подключение к облачному хранилищу."""
        pass

    @abstractmethod
    async def check_connection(self) -> bool:
        """Проверка подключения к облачному хранилищу."""
        pass

    @abstractmethod
    async def list_directories(self, path: str = "/") -> List[str]:
        """Получение списка директорий."""
        pass

    @abstractmethod
    async def download_file(self, remote_path: str, local_path: Union[str, Path]) -> bool:
        """Скачивание файла."""
        pass

    @abstractmethod
    async def upload_file(self, local_path: Union[str, Path], remote_path: str) -> bool:
        """Загрузка файла."""
        pass

    @abstractmethod
    async def search_directories(self, name: str, path: str = "/") -> List[str]:
        """Поиск директорий по имени."""
        pass

    async def disconnect(self):
        """Отключение от облачного хранилища."""
        self._client = None
        self._is_connected = False
