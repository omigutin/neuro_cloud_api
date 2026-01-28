import yadisk
from pathlib import Path
from typing import Union, List, Dict, Any

from .base_source_async import BaseSourceAsync
from .source_type import SourceType
from ..errors import ConnectionError, AuthenticationError, DownloadError, UploadError


class YadiskSourceAsync(BaseSourceAsync):
    """Асинхронный клиент Яндекс.Диска."""

    def __init__(self, token: str):
        super().__init__(token, source_type=SourceType.YANDEX_DISK)
        self._client = yadisk.AsyncClient(token=token)

    async def connect(self) -> bool:
        """Подключение к Яндекс.Диску."""
        try:
            if await self.check_connection():
                self._is_connected = True
                return True
            return False
        except Exception as e:
            raise ConnectionError(f"Ошибка подключения к Яндекс.Диску: {e}") from e

    async def check_connection(self) -> bool:
        """Проверка подключения к Яндекс.Диску."""
        if self._client is None:
            return False
        try:
            result = await self._client.check_token()
            return bool(result)
        except yadisk.exceptions.UnauthorizedError:
            raise AuthenticationError("Неверный токен Яндекс.Диска")
        except Exception as e:
            raise ConnectionError(f"Ошибка проверки подключения: {e}") from e

    async def list_directories(self, path: str = "/") -> List[str]:
        """
        Получение списка директорий на Яндекс.Диске.

        Args:
            path: Путь к директории

        Returns:
            Список путей к директориям
        """
        result = []
        try:
            async for item in self._client.listdir(path):
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "dir":
                    result.append(item.get("path", ""))
        except Exception as e:
            raise ConnectionError(f"Ошибка получения списка директорий {path}: {e}") from e
        return result

    async def download_file(self, remote_path: str, local_path: Union[str, Path]) -> bool:
        """
        Скачивание файла с Яндекс.Диска.

        Args:
            remote_path: Путь к файлу на Яндекс.Диске
            local_path: Локальный путь для сохранения

        Returns:
            True если скачивание успешно, иначе False
        """
        try:
            local_path = Path(local_path)
            local_path.parent.mkdir(parents=True, exist_ok=True)
            await self._client.download(remote_path, str(local_path))
            return True
        except Exception as e:
            raise DownloadError(f"Ошибка скачивания файла {remote_path}: {e}") from e

    async def upload_file(self, local_path: Union[str, Path], remote_path: str) -> bool:
        """
        Загрузка файла на Яндекс.Диск.

        Args:
            local_path: Локальный путь к файлу
            remote_path: Путь на Яндекс.Диске

        Returns:
            True если загрузка успешна, иначе False
        """
        try:
            local_path = Path(local_path)
            if not local_path.exists():
                raise UploadError(f"Локальный файл не найден: {local_path}")
            await self._client.upload(str(local_path), remote_path)
            return True
        except UploadError:
            raise
        except Exception as e:
            raise UploadError(f"Ошибка загрузки файла {local_path}: {e}") from e

    async def search_directories(self, name: str, path: str = "/") -> List[str]:
        """
        Поиск директорий по имени на Яндекс.Диске.

        Args:
            name: Имя для поиска
            path: Путь для поиска

        Returns:
            Список путей к найденным директориям
        """
        result = []
        try:
            async for item in self._client.listdir(path):
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "dir" and name.lower() in item.get("name", "").lower():
                    result.append(item.get("path", ""))
        except Exception as e:
            raise ConnectionError(f"Ошибка поиска директорий {name} в {path}: {e}") from e
        return result

    async def disconnect(self):
        """Отключение от облачного хранилища."""
        if self._client:
            await self._client.close()
        self._client = None
        self._is_connected = False
