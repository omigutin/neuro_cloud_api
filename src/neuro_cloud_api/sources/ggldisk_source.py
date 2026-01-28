from pathlib import Path
from typing import Union, List

from .base_source import BaseSource
from .source_type import SourceType
from ..errors import SourceNotImplementedError


class GoogleDriveSource(BaseSource):
    """Класс для работы с Google Drive (заглушка)."""

    def __init__(self, token: str):
        """
        Инициализация клиента Google Drive.

        Args:
            token: OAuth-токен Google Drive
        """
        super().__init__(token, source_type=SourceType.GOOGLE_DRIVE)
        self._client = None

    def connect(self) -> bool:
        """Подключение к Google Drive."""
        raise SourceNotImplementedError("Google Drive источник еще не реализован")

    def check_connection(self) -> bool:
        """Проверка подключения к Google Drive."""
        raise SourceNotImplementedError("Google Drive источник еще не реализован")

    def list_directories(self, path: str = "/") -> List[str]:
        """Получение списка директорий."""
        raise SourceNotImplementedError("Google Drive источник еще не реализован")

    def download_file(self, remote_path: str, local_path: Union[str, Path]) -> bool:
        """Скачивание файла."""
        raise SourceNotImplementedError("Google Drive источник еще не реализован")

    def upload_file(self, local_path: Union[str, Path], remote_path: str) -> bool:
        """Загрузка файла."""
        raise SourceNotImplementedError("Google Drive источник еще не реализован")

    def search_directories(self, name: str, path: str = "/") -> List[str]:
        """Поиск директорий по имени."""
        raise SourceNotImplementedError("Google Drive источник еще не реализован")
