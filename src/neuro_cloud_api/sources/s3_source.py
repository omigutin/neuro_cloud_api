from pathlib import Path
from typing import Union, List

from .base_source import BaseSource
from .source_type import SourceType
from ..errors import SourceNotImplementedError


class S3Source(BaseSource):
    """Класс для работы с Amazon S3 (заглушка)."""

    def __init__(self, token: str):
        """
        Инициализация клиента S3.

        Args:
            token: Токен для доступа к S3
        """
        super().__init__(token, source_type=SourceType.S3)
        self._client = None

    def connect(self) -> bool:
        """Подключение к S3."""
        raise SourceNotImplementedError("S3 источник еще не реализован")

    def check_connection(self) -> bool:
        """Проверка подключения к S3."""
        raise SourceNotImplementedError("S3 источник еще не реализован")

    def list_directories(self, path: str = "/") -> List[str]:
        """Получение списка директорий."""
        raise SourceNotImplementedError("S3 источник еще не реализован")

    def download_file(self, remote_path: str, local_path: Union[str, Path]) -> bool:
        """Скачивание файла."""
        raise SourceNotImplementedError("S3 источник еще не реализован")

    def upload_file(self, local_path: Union[str, Path], remote_path: str) -> bool:
        """Загрузка файла."""
        raise SourceNotImplementedError("S3 источник еще не реализован")

    def search_directories(self, name: str, path: str = "/") -> List[str]:
        """Поиск директорий по имени."""
        raise SourceNotImplementedError("S3 источник еще не реализован")
