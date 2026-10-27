import warnings
from abc import ABC, abstractmethod
from pathlib import Path
from types import TracebackType
from typing import Any, AsyncIterator, List, Optional, Type, Union

from .source_type import SourceType
from ..models import StorageItem


class BaseSourceAsync(ABC):
    """Базовый контракт асинхронного storage-источника.

    Функционально идентичен :class:`BaseSource`, но все операции — корутины,
    а ``iter_items`` — async-генератор. Семантика совпадает с синхронной.
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
    async def connect(self) -> None:
        """Полное подключение/проверка доступа. Бросает конкретное исключение при проблеме."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Отключение и освобождение ресурсов клиента."""

    @abstractmethod
    async def check_connection(self) -> bool:
        """Health/status-check. Возвращает ``True``/``False`` и НЕ бросает."""

    async def __aenter__(self) -> "BaseSourceAsync":
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        await self.disconnect()

    # ── Metadata / listing ──────────────────────────────────────────────────

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """True, если объект по пути существует."""

    @abstractmethod
    async def get_item(self, path: str) -> StorageItem:
        """Metadata объекта. Бросает ``RemoteNotFoundError``, если объекта нет."""

    @abstractmethod
    def iter_items(self, path: str = "/") -> AsyncIterator[StorageItem]:
        """Ленивый async-обход содержимого каталога (файлы и каталоги)."""

    async def list_items(self, path: str = "/") -> List[StorageItem]:
        """Материализованный список содержимого каталога."""
        return [item async for item in self.iter_items(path)]

    # ── Операции ────────────────────────────────────────────────────────────

    @abstractmethod
    async def mkdir(self, path: str, *, parents: bool = True, exist_ok: bool = True) -> None:
        """Создать каталог (при ``parents`` — вместе с родителями)."""

    @abstractmethod
    async def upload_file(
        self,
        local_path: Union[str, Path],
        remote_path: str,
        *,
        overwrite: bool = False,
        create_parents: bool = True,
    ) -> None:
        """Загрузить локальный файл на remote."""

    @abstractmethod
    async def download_file(
        self,
        remote_path: str,
        local_path: Union[str, Path],
        *,
        overwrite: bool = False,
        create_parents: bool = True,
    ) -> None:
        """Скачать remote-файл локально."""

    @abstractmethod
    async def delete(self, path: str, *, recursive: bool = False) -> None:
        """Удалить объект из активного namespace хранилища."""

    @abstractmethod
    async def move(self, source: str, destination: str, *, overwrite: bool = False) -> None:
        """Переместить объект. ``destination`` — полный целевой path."""

    @abstractmethod
    async def copy(self, source: str, destination: str, *, overwrite: bool = False) -> None:
        """Скопировать объект. ``destination`` — полный целевой path."""

    # ── Deprecated convenience ──────────────────────────────────────────────

    async def list_directories(self, path: str = "/") -> List[str]:
        """DEPRECATED: используйте :meth:`list_items`. Возвращает пути каталогов."""
        warnings.warn(
            "list_directories устарел; используйте list_items/iter_items",
            DeprecationWarning,
            stacklevel=2,
        )
        return [item.path async for item in self.iter_items(path) if item.is_dir]

    async def search_directories(self, name: str, path: str = "/") -> List[str]:
        """DEPRECATED convenience: client-side substring-поиск каталогов (non-recursive)."""
        warnings.warn(
            "search_directories устарел; используйте list_items/iter_items с фильтрацией",
            DeprecationWarning,
            stacklevel=2,
        )
        needle = name.lower()
        return [
            item.path
            async for item in self.iter_items(path)
            if item.is_dir and needle in item.name.lower()
        ]
