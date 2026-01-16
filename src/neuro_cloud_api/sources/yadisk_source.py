import yadisk

from pathlib import Path
from typing import Union, List

from .base_source import BaseSource
from .source_type import SourceType


class YadiskSource(BaseSource):
    """Класс для работы с Яндекс.Диском."""

    def __init__(self, token: str):
        """
        Инициализация клиента Яндекс.Диска.

        Args:
            token: OAuth-токен Яндекс.Диска
        """
        super().__init__(token, source_type=SourceType.YANDEX_DISK) # Здесь должен получать конфиг
        self.client = yadisk.Client(token=token)

    def connect(self) -> bool:
        """Подключение к Яндекс.Диску."""
        try:
            if self.check_connection():
                self.is_connected = True
                print("Успешно подключено к Яндекс.Диску")
                return True
            else:
                print("Не удалось подключиться к Яндекс.Диску")
                return False
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False

    def check_connection(self) -> bool:
        """Проверка подключения к Яндекс.Диску."""
        try:
            if self.client.check_token():
                return True
        except yadisk.exceptions.UnauthorizedError:
            print("Неверный токен Яндекс.Диска")
            return False
        except Exception as e:
            print(f"Ошибка проверки подключения: {e}")
            return False

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
            for item in self.client.listdir(path):
                if item["type"] == "dir":
                    result.append(item["path"])
        except Exception as e:
            print(f"Ошибка получения списка директорий {path}: {e}")
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
            for item in self.client.listdir(path):
                if item["type"] == "dir" and name.lower() in item["name"].lower():
                    result.append(item["path"])
        except Exception as e:
            print(f"Ошибка поиска директорий {name} в {path}: {e}")
        return result

    def download_file(self, remote_path: str, local_path: Union[str, Path]) -> bool:
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
            local_path.parent.mkdir(parents=True, exist_ok=True) # Вынести создание дирректории в отдельный метод

            self.client.download(remote_path, str(local_path))
            print(f"Файл {remote_path} скачан в {local_path}")
            return True
        except Exception as e:
            print(f"Ошибка скачивания файла {remote_path}: {e}")
            return False

    def _ensure_directory_exists(self, remote_path: str) -> None:
        """
        Создает директорию на Яндекс.Диске, если она не существует.

        Args:
            remote_path: Путь к директории на Яндекс.Диске
        """
        try:
            if not self.client.exists(remote_path):
                # Создаем родительские директории рекурсивно
                parent = Path(remote_path).parent
                if str(parent) != "/" and str(parent) != ".":
                    self._ensure_directory_exists(str(parent))
                self.client.mkdir(remote_path)
        except Exception as e:
            print(f"Ошибка создания директории {remote_path}: {e}")

    def upload_file(self, local_path: Union[str, Path], remote_path: str) -> bool:
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
                print(f"Локальный файл не найден: {local_path}")
                return False

            # Создаем директорию на Яндекс.Диске, если ее нет
            remote_dir = Path(remote_path).parent
            if str(remote_dir) != "." and str(remote_dir) != "/":
                self._ensure_directory_exists(str(remote_dir))

            self.client.upload(str(local_path), remote_path)
            print(f"Файл {local_path} загружен в {remote_path}")
            return True
        except Exception as e:
            print(f"Ошибка загрузки файла {local_path}: {e}")
            return False



