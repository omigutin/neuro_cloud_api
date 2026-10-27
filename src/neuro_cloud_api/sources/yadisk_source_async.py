import logging
from pathlib import Path

import yadisk
from typing import AsyncIterator, Union

from . import _yadisk_common as _c
from .base_source_async import BaseSourceAsync
from .source_type import SourceType
from ..models import StorageItem
from ..paths import normalize_remote_path, remote_parent
from ..errors import (
    CloudAuthenticationError,
    RemoteConflictError,
    RemoteExistsError,
    LocalNotFoundError,
    LocalExistsError,
    LocalFileError,
)

_exc = yadisk.exceptions
_log = logging.getLogger(__name__)


class YadiskSourceAsync(BaseSourceAsync):
    """Асинхронный источник Яндекс.Диска (semantics совпадает с YadiskSource)."""

    _client: yadisk.AsyncClient

    def __init__(self, token: str):
        super().__init__(token, source_type=SourceType.YANDEX_DISK)
        self._client = yadisk.AsyncClient(token=token)

    # ── Lifecycle ───────────────────────────────────────────────────────────

    async def connect(self) -> None:
        try:
            ok = await self._client.check_token()
        except _exc.UnauthorizedError as e:
            raise CloudAuthenticationError("Неверный токен Яндекс.Диска") from e
        except Exception as e:
            raise _c.translate_error(e) from e
        if not ok:
            raise CloudAuthenticationError("Неверный токен Яндекс.Диска")
        self._is_connected = True

    async def check_connection(self) -> bool:
        try:
            return bool(await self._client.check_token())
        except Exception:
            # Контракт health-check: не бросать; причину оставляем в логе.
            _log.debug("Проверка подключения к Яндекс.Диску не прошла", exc_info=True)
            return False

    async def disconnect(self) -> None:
        try:
            await self._client.close()
        except Exception:
            # Ошибка закрытия не должна подменять исходную ошибку из блока async with.
            _log.warning("Не удалось закрыть клиент Яндекс.Диска", exc_info=True)
        self._is_connected = False

    # ── Metadata / listing ──────────────────────────────────────────────────

    @_c.translating_async
    async def exists(self, path: str) -> bool:
        return bool(await self._client.exists(normalize_remote_path(path)))

    @_c.translating_async
    async def get_item(self, path: str) -> StorageItem:
        resource = await self._client.get_meta(normalize_remote_path(path))
        return _c.to_storage_item(resource)

    async def iter_items(self, path: str = "/") -> AsyncIterator[StorageItem]:
        remote = normalize_remote_path(path)
        try:
            async for resource in self._client.listdir(remote):
                yield _c.to_storage_item(resource)
        except Exception as e:
            raise _c.translate_error(e) from e

    # ── Операции ────────────────────────────────────────────────────────────

    @_c.translating_async
    async def mkdir(self, path: str, *, parents: bool = True, exist_ok: bool = True) -> None:
        remote = normalize_remote_path(path)
        if parents:
            parent = remote_parent(remote)
            if parent != remote:
                await self._ensure_dir(parent)
        try:
            await self._client.mkdir(remote)
        except (_exc.PathExistsError, _exc.DirectoryExistsError):
            if not exist_ok:
                raise RemoteExistsError(f"Каталог уже существует: {remote}")

    @_c.translating_async
    async def upload_file(
        self,
        local_path: Union[str, Path],
        remote_path: str,
        *,
        overwrite: bool = False,
        create_parents: bool = True,
    ) -> None:
        local = Path(local_path)
        remote = normalize_remote_path(remote_path)
        if not local.exists():
            raise LocalNotFoundError(f"Локальный файл не найден: {local}")
        if not local.is_file():
            raise LocalFileError(f"Источник не является файлом: {local}")
        if create_parents:
            parent = remote_parent(remote)
            if parent != remote:
                await self._ensure_dir(parent)
        try:
            await self._client.upload(str(local), remote, overwrite=overwrite)
        except (_exc.PathExistsError, _exc.DirectoryExistsError):
            raise RemoteExistsError(f"Объект уже существует: {remote}")

    @_c.translating_async
    async def download_file(
        self,
        remote_path: str,
        local_path: Union[str, Path],
        *,
        overwrite: bool = False,
        create_parents: bool = True,
    ) -> None:
        remote = normalize_remote_path(remote_path)
        local = Path(local_path)
        if local.exists() and not overwrite:
            raise LocalExistsError(f"Локальный файл уже существует: {local}")
        if create_parents:
            local.parent.mkdir(parents=True, exist_ok=True)
        await self._client.download(remote, str(local))

    @_c.translating_async
    async def delete(self, path: str, *, recursive: bool = False) -> None:
        remote = normalize_remote_path(path)
        if not recursive and await self._client.is_dir(remote) and not await self._is_empty_dir(remote):
            raise RemoteConflictError(f"Каталог не пуст (recursive=False): {remote}")
        await self._client.remove(remote)

    @_c.translating_async
    async def move(self, source: str, destination: str, *, overwrite: bool = False) -> None:
        await self._client.move(
            normalize_remote_path(source),
            normalize_remote_path(destination),
            overwrite=overwrite,
        )

    @_c.translating_async
    async def copy(self, source: str, destination: str, *, overwrite: bool = False) -> None:
        await self._client.copy(
            normalize_remote_path(source),
            normalize_remote_path(destination),
            overwrite=overwrite,
        )

    # ── Внутреннее ──────────────────────────────────────────────────────────

    async def _ensure_dir(self, remote: str) -> None:
        """Идемпотентно создаёт каталог и всех его предков (canonical путь)."""
        if remote in ("/", ""):
            return
        if await self._client.exists(remote):
            return
        parent = remote_parent(remote)
        if parent != remote:
            await self._ensure_dir(parent)
        try:
            await self._client.mkdir(remote)
        except (_exc.PathExistsError, _exc.DirectoryExistsError):
            pass

    async def _is_empty_dir(self, remote: str) -> bool:
        async for _ in self._client.listdir(remote):
            return False
        return True
