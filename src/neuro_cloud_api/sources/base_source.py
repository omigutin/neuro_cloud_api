import warnings
from abc import ABC, abstractmethod
from pathlib import Path
from types import TracebackType
from typing import Any, Iterator, List, Optional, Type, Union

from .source_type import SourceType
from ..models import StorageItem


class BaseSource(ABC):
    """Базовый контракт синхронного storage-источника.

    Провайдеры реализуют небольшой набор примитивов; производные операции
    (``list_items``, deprecated listing, context manager) определены здесь
    поверх абстрактного ``iter_items`` и одинаковы для всех провайдеров.
    """

    def __init__(self, token: str, source_type: SourceType):
        self._token = token
        self._source_type = source_type
        self._client: Optional[Any] = None
        self._is_connected = False

    # ── Свойства ────────────────────────────────────────────────────────────

    @property
    def token(self) -> str:
        return self._token

    @property
    def source_type(self) -> SourceType:
        return self._source_type

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    # ── Lifecycle ───────────────────────────────────────────────────────────

    @abstractmethod
    def connect(self) -> None:
        """Полное подключение/проверка доступа. Бросает конкретное исключение при проблеме."""

    @abstractmethod
    def disconnect(self) -> None:
        """Отключение и освобождение ресурсов клиента."""

    @abstractmethod
    def check_connection(self) -> bool:
        """Health/status-check. Возвращает ``True``/``False`` и НЕ бросает."""

    def __enter__(self) -> "BaseSource":
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self.disconnect()

    # ── Metadata / listing ──────────────────────────────────────────────────

    @abstractmethod
    def exists(self, path: str) -> bool:
        """True, если объект по пути существует."""

    @abstractmethod
    def get_item(self, path: str) -> StorageItem:
        """Metadata объекта. Бросает ``RemoteNotFoundError``, если объекта нет."""

    @abstractmethod
    def iter_items(self, path: str = "/") -> Iterator[StorageItem]:
        """Ленивый обход содержимого каталога (файлы и каталоги)."""

    def list_items(self, path: str = "/") -> List[StorageItem]:
        """Материализованный список содержимого каталога."""
        return list(self.iter_items(path))

    # ── Операции ────────────────────────────────────────────────────────────

    @abstractmethod
    def mkdir(self, path: str, *, parents: bool = True, exist_ok: bool = True) -> None:
        """Создать каталог (при ``parents`` — вместе с родителями)."""

    @abstractmethod
    def upload_file(
        self,
        local_path: Union[str, Path],
        remote_path: str,
        *,
        overwrite: bool = False,
        create_parents: bool = True,
    ) -> None:
        """Загрузить локальный файл на remote."""

    @abstractmethod
    def download_file(
        self,
        remote_path: str,
        local_path: Union[str, Path],
        *,
        overwrite: bool = False,
        create_parents: bool = True,
    ) -> None:
        """Скачать remote-файл локально."""

    @abstractmethod
    def delete(self, path: str, *, recursive: bool = False) -> None:
        """Удалить объект из активного namespace хранилища."""

    @abstractmethod
    def move(self, source: str, destination: str, *, overwrite: bool = False) -> None:
        """Переместить объект. ``destination`` — полный целевой path."""

    @abstractmethod
    def copy(self, source: str, destination: str, *, overwrite: bool = False) -> None:
        """Скопировать объект. ``destination`` — полный целевой path."""

    # ── Deprecated convenience ──────────────────────────────────────────────

    def list_directories(self, path: str = "/") -> List[str]:
        """DEPRECATED: используйте :meth:`list_items`. Возвращает пути каталогов."""
        warnings.warn(
            "list_directories устарел; используйте list_items/iter_items",
            DeprecationWarning,
            stacklevel=2,
        )
        return [item.path for item in self.iter_items(path) if item.is_dir]

    def search_directories(self, name: str, path: str = "/") -> List[str]:
        """DEPRECATED convenience: client-side substring-поиск каталогов (non-recursive)."""
        warnings.warn(
            "search_directories устарел; используйте list_items/iter_items с фильтрацией",
            DeprecationWarning,
            stacklevel=2,
        )
        needle = name.lower()
        return [
            item.path
            for item in self.iter_items(path)
            if item.is_dir and needle in item.name.lower()
        ]
