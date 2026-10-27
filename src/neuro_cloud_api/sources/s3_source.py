from pathlib import Path
from typing import Iterator, NoReturn, Union

from .base_source import BaseSource
from .source_type import SourceType
from ..errors import SourceNotImplementedError
from ..models import StorageItem

_MESSAGE = "S3 источник еще не реализован"


def _not_implemented() -> NoReturn:
    raise SourceNotImplementedError(_MESSAGE)


class S3Source(BaseSource):
    """Источник Amazon S3 (заглушка): контракт BaseSource, все операции бросают SourceNotImplementedError."""

    def __init__(self, token: str):
        super().__init__(token, source_type=SourceType.S3)

    def connect(self) -> None:
        _not_implemented()

    def disconnect(self) -> None:
        self._is_connected = False

    def check_connection(self) -> bool:
        return False

    def exists(self, path: str) -> bool:
        _not_implemented()

    def get_item(self, path: str) -> StorageItem:
        _not_implemented()

    def iter_items(self, path: str = "/") -> Iterator[StorageItem]:
        _not_implemented()

    def mkdir(self, path: str, *, parents: bool = True, exist_ok: bool = True) -> None:
        _not_implemented()

    def upload_file(
        self,
        local_path: Union[str, Path],
        remote_path: str,
        *,
        overwrite: bool = False,
        create_parents: bool = True,
    ) -> None:
        _not_implemented()

    def download_file(
        self,
        remote_path: str,
        local_path: Union[str, Path],
        *,
        overwrite: bool = False,
        create_parents: bool = True,
    ) -> None:
        _not_implemented()

    def delete(self, path: str, *, recursive: bool = False) -> None:
        _not_implemented()

    def move(self, source: str, destination: str, *, overwrite: bool = False) -> None:
        _not_implemented()

    def copy(self, source: str, destination: str, *, overwrite: bool = False) -> None:
        _not_implemented()
