import yadisk
from pathlib import Path, PurePosixPath
from typing import Union, List, Dict, Any

from .base_source import BaseSource
from .source_type import SourceType
from ..errors import ConnectionError, AuthenticationError, UploadError, DownloadError


class YadiskSource(BaseSource):
    """Класс для работы с Яндекс.Диском."""

    def __init__(self, token: str):
        """
        Инициализация клиента Яндекс.Диска.

        Args:
            token: OAuth-токен Яндекс.Диска
        """
        super().__init__(token, source_type=SourceType.YANDEX_DISK)
        self._client = yadisk.Client(token=token)

    def connect(self) -> bool:
        """Подключение к Яндекс.Диску."""
        try:
            if self.check_connection():
                self._is_connected = True
                return True
            else:
                return False
        except (AuthenticationError, ConnectionError):
            raise
        except Exception as e:
            raise ConnectionError(f"Ошибка подключения к Яндекс.Диску: {e}") from e

    def check_connection(self) -> bool:
        """Проверка подключения к Яндекс.Диску."""
        try:
            result = self._client.check_token()
            if result:
                return True
            else:
                return False
        except yadisk.exceptions.UnauthorizedError:
            raise AuthenticationError("Неверный токен Яндекс.Диска")
        except Exception as e:
            raise ConnectionError(f"Ошибка проверки подключения: {e}") from e

    def list_directories(self, path: str = "/") -> List[str]:
        """
        Получение списка директорий на Яндекс.Диске.

        Args:
            path: Путь к директории

        Returns:
            Список путей к директориям
        """
        result = []
        try:
            for item in self._client.listdir(path):
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "dir":
                    result.append(item.get("path", ""))
        except Exception as e:
            raise ConnectionError(f"Ошибка получения списка директорий {path}: {e}") from e
        return result

    def search_directories(self, name: str, path: str = "/") -> List[str]:
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
            for item in self._client.listdir(path):
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "dir" and name.lower() in item.get("name", "").lower():
                    result.append(item.get("path", ""))
        except Exception as e:
            raise ConnectionError(f"Ошибка поиска директорий {name} в {path}: {e}") from e
        return result

    def download_file(self, remote_path: str, local_path: Union[str, Path]) -> bool:
        """
        Скачивание файла с Яндекс.Диска.

        Args:
            remote_path: Путь к файлу на Яндекс.Диске
            local_path: Локальный путь для сохранения

        Returns:
            True если скачивание успешно, иначе False

        Raises:
            DownloadError: При ошибке скачивания
        """
        try:
            local_path = Path(local_path)
            local_path.parent.mkdir(parents=True, exist_ok=True)

            self._client.download(remote_path, str(local_path))
            return True
        except Exception as e:
            raise DownloadError(f"Ошибка скачивания файла {remote_path}: {e}") from e

    def _ensure_directory_exists(self, remote_path: str) -> None:
        """
        Создает директорию на Яндекс.Диске, если она не существует.

        Args:
            remote_path: Путь к директории на Яндекс.Диске

        Raises:
            ConnectionError: При ошибке создания директории
        """
        try:
            if not self._client.exists(remote_path):
                # Создаем родительские директории рекурсивно
                parent = PurePosixPath(remote_path).parent
                if str(parent) != "/" and str(parent) != ".":
                    self._ensure_directory_exists(str(parent))
                self._client.mkdir(remote_path)
        except Exception as e:
            raise ConnectionError(f"Ошибка создания директории {remote_path}: {e}") from e

    def upload_file(self, local_path: Union[str, Path], remote_path: str) -> bool:
        """
        Загрузка файла на Яндекс.Диск.

        Args:
            local_path: Локальный путь к файлу
            remote_path: Путь на Яндекс.Диске

        Returns:
            True если загрузка успешна, иначе False

        Raises:
            FileNotFoundError: Если локальный файл не найден (встроенное исключение Python)
            UploadError: При ошибке загрузки
        """
        try:
            local_path = Path(local_path)
            if not local_path.exists():
                raise FileNotFoundError(f"Локальный файл не найден: {local_path}")

            # Создаем директорию на Яндекс.Диске, если ее нет
            remote_dir = PurePosixPath(remote_path).parent
            if str(remote_dir) != "." and str(remote_dir) != "/":
                self._ensure_directory_exists(str(remote_dir))

            self._client.upload(str(local_path), remote_path)
            return True
        except FileNotFoundError:
            raise
        except Exception as e:
            raise UploadError(f"Ошибка загрузки файла {local_path}: {e}") from e
