"""Общая Yandex-специфичная склейка для sync и async источников.

Здесь сосредоточено всё, что должно вести себя ОДИНАКОВО в синхронной и
асинхронной реализациях, чтобы не возникал parity-долг:

* приведение пути Яндекс.Диска к canonical виду (срез префикса ``disk:``);
* маппинг ``yadisk`` resource-объекта → provider-independent ``StorageItem``;
* трансляция исключений ``yadisk``/локальной ФС → доменную иерархию;
* декораторы, оборачивающие вызовы провайдера этой трансляцией.

``yadisk`` возвращает resource-объекты (``SyncResourceObject`` /
``AsyncResourceObject``) с доступом по атрибутам — не ``dict``.
"""

from functools import wraps
from typing import Any

import yadisk

from ..errors import (
    NeuroCloudError,
    CloudAuthenticationError,
    CloudConnectionError,
    CloudRateLimitError,
    RemoteNotFoundError,
    RemoteConflictError,
    RemoteExistsError,
    RemotePermissionError,
    LocalFileError,
    LocalNotFoundError,
    LocalExistsError,
    LocalPermissionError,
    ProviderError,
)
from ..models import StorageItem, StorageItemKind

__all__ = [
    "strip_disk_prefix",
    "to_storage_item",
    "translate_error",
    "translating",
    "translating_async",
]

_exc = yadisk.exceptions


def strip_disk_prefix(path: str) -> str:
    """Приводит путь Яндекс.Диска к canonical POSIX-виду.

    ``yadisk`` отдаёт пути с префиксом ``disk:`` (особенность API Яндекс.Диска),
    который не должен протекать в provider-independent контракт::

        "disk:/Foo/bar" -> "/Foo/bar"
        "disk:"         -> "/"
    """
    if not path:
        return path
    if path.startswith("disk:"):
        rest = path[len("disk:"):]
        return rest or "/"
    return path


def to_storage_item(resource: Any) -> StorageItem:
    """Маппит ``yadisk`` resource-объект в ``StorageItem``.

    ``checksum`` заполняется только для файлов, у которых Яндекс реально
    отдаёт md5 (известный алгоритм); иначе оба checksum-поля остаются ``None``.
    """
    kind = (
        StorageItemKind.DIRECTORY
        if getattr(resource, "type", None) == "dir"
        else StorageItemKind.FILE
    )

    md5 = getattr(resource, "md5", None)
    checksum = md5 if (kind is StorageItemKind.FILE and md5) else None
    checksum_algorithm = "md5" if checksum else None

    return StorageItem(
        name=getattr(resource, "name", "") or "",
        path=strip_disk_prefix(getattr(resource, "path", "") or ""),
        kind=kind,
        size=getattr(resource, "size", None),
        modified_at=getattr(resource, "modified", None),
        created_at=getattr(resource, "created", None),
        checksum=checksum,
        checksum_algorithm=checksum_algorithm,
        mime_type=getattr(resource, "mime_type", None),
    )


def translate_error(exc: BaseException) -> NeuroCloudError:
    """Транслирует исключение ``yadisk``/локальной ФС в доменное.

    Порядок проверок важен: более специфичные классы идут раньше своих
    базовых (напр. ``PathExistsError`` до ``ConflictError``).
    """
    if isinstance(exc, NeuroCloudError):
        return exc

    # Локальная файловая система
    if isinstance(exc, FileNotFoundError):
        return LocalNotFoundError(str(exc))
    if isinstance(exc, FileExistsError):
        return LocalExistsError(str(exc))
    if isinstance(exc, PermissionError):
        return LocalPermissionError(str(exc))
    if isinstance(exc, OSError):
        return LocalFileError(str(exc))

    # yadisk / удалённый провайдер
    if isinstance(exc, _exc.UnauthorizedError):
        return CloudAuthenticationError(str(exc))
    if isinstance(exc, _exc.ForbiddenError):
        return RemotePermissionError(str(exc))
    if isinstance(exc, (_exc.PathExistsError, _exc.DirectoryExistsError)):
        return RemoteExistsError(str(exc))
    if isinstance(exc, (_exc.PathNotFoundError, _exc.NotFoundError)):
        return RemoteNotFoundError(str(exc))
    if isinstance(exc, _exc.TooManyRequestsError):
        return CloudRateLimitError(str(exc))
    if isinstance(exc, (_exc.ConflictError, _exc.LockedError)):
        return RemoteConflictError(str(exc))
    if isinstance(exc, _exc.RequestError):
        # transport: соединение, таймаут, DNS, редиректы
        return CloudConnectionError(str(exc))
    if isinstance(exc, _exc.YaDiskError):
        # 5xx, InsufficientStorage, WrongResourceType, InvalidResponse и пр.
        return ProviderError(str(exc))

    return ProviderError(str(exc))


def translating(fn):
    """Декоратор sync-метода: транслирует любые ошибки провайдера в доменные."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except NeuroCloudError:
            raise
        except Exception as e:
            raise translate_error(e) from e

    return wrapper


def translating_async(fn):
    """Декоратор async-метода (корутины): та же трансляция ошибок."""

    @wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except NeuroCloudError:
            raise
        except Exception as e:
            raise translate_error(e) from e

    return wrapper
