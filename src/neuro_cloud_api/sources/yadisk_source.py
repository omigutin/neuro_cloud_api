import logging
from pathlib import Path

import yadisk
from typing import Iterator, Union

from . import _yadisk_common as _c
from .base_source import BaseSource
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


class YadiskSource(BaseSource):
    """Синхронный источник Яндекс.Диска."""

    _client: yadisk.Client

    def __init__(self, token: str):
        super().__init__(token, source_type=SourceType.YANDEX_DISK)
        self._client = yadisk.Client(token=token)

    # ── Lifecycle ───────────────────────────────────────────────────────────

    def connect(self) -> None:
        try:
            ok = self._client.check_token()
        except _exc.UnauthorizedError as e:
            raise CloudAuthenticationError("Неверный токен Яндекс.Диска") from e
        except Exception as e:
            raise _c.translate_error(e) from e
        if not ok:
            raise CloudAuthenticationError("Неверный токен Яндекс.Диска")
        self._is_connected = True

    def check_connection(self) -> bool:
        try:
            return bool(self._client.check_token())
        except Exception:
            # Контракт health-check: не бросать; причину оставляем в логе.
            _log.debug("Проверка подключения к Яндекс.Диску не прошла", exc_info=True)
            return False

    def disconnect(self) -> None:
        try:
            self._client.close()
        except Exception:
            # Ошибка закрытия не должна подменять исходную ошибку из блока with.
            _log.warning("Не удалось закрыть клиент Яндекс.Диска", exc_info=True)
        self._is_connected = False

    # ── Metadata / listing ──────────────────────────────────────────────────

    @_c.translating
    def exists(self, path: str) -> bool:
        return bool(self._client.exists(normalize_remote_path(path)))

    @_c.translating
    def get_item(self, path: str) -> StorageItem:
        resource = self._client.get_meta(normalize_remote_path(path))
        return _c.to_storage_item(resource)

    def iter_items(self, path: str = "/") -> Iterator[StorageItem]:
        remote = normalize_remote_path(path)
        try:
            for resource in self._client.listdir(remote):
                yield _c.to_storage_item(resource)
        except Exception as e:
            raise _c.translate_error(e) from e

    # ── Операции ────────────────────────────────────────────────────────────

    @_c.translating
    def mkdir(self, path: str, *, parents: bool = True, exist_ok: bool = True) -> None:
        remote = normalize_remote_path(path)
        if parents:
            parent = remote_parent(remote)
            if parent != remote:
                self._ensure_dir(parent)
        try:
            self._client.mkdir(remote)
        except (_exc.PathExistsError, _exc.DirectoryExistsError):
            if not exist_ok:
                raise RemoteExistsError(f"Каталог уже существует: {remote}")

    @_c.translating
    def upload_file(
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
                self._ensure_dir(parent)
        try:
            self._client.upload(str(local), remote, overwrite=overwrite)
        except (_exc.PathExistsError, _exc.DirectoryExistsError):
            raise RemoteExistsError(f"Объект уже существует: {remote}")

    @_c.translating
    def download_file(
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
        self._client.download(remote, str(local))

    @_c.translating
    def delete(self, path: str, *, recursive: bool = False) -> None:
        remote = normalize_remote_path(path)
        if not recursive and self._client.is_dir(remote) and not self._is_empty_dir(remote):
            raise RemoteConflictError(f"Каталог не пуст (recursive=False): {remote}")
        self._client.remove(remote)

    @_c.translating
    def move(self, source: str, destination: str, *, overwrite: bool = False) -> None:
        self._client.move(
            normalize_remote_path(source),
            normalize_remote_path(destination),
            overwrite=overwrite,
        )

    @_c.translating
    def copy(self, source: str, destination: str, *, overwrite: bool = False) -> None:
        self._client.copy(
            normalize_remote_path(source),
            normalize_remote_path(destination),
            overwrite=overwrite,
        )

    # ── Внутреннее ──────────────────────────────────────────────────────────

    def _ensure_dir(self, remote: str) -> None:
        """Идемпотентно создаёт каталог и всех его предков (canonical путь)."""
        if remote in ("/", ""):
            return
        if self._client.exists(remote):
            return
        parent = remote_parent(remote)
        if parent != remote:
            self._ensure_dir(parent)
        try:
            self._client.mkdir(remote)
        except (_exc.PathExistsError, _exc.DirectoryExistsError):
            pass

    def _is_empty_dir(self, remote: str) -> bool:
        for _ in self._client.listdir(remote):
            return False
        return True
