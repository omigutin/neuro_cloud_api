"""Provider-independent доменная модель storage-объектов."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

__all__ = ["StorageItemKind", "StorageItem"]


class StorageItemKind(str, Enum):
    """Тип storage-объекта (provider-independent)."""

    FILE = "file"
    DIRECTORY = "directory"


@dataclass(frozen=True, slots=True)
class StorageItem:
    """Единица хранилища: файл или каталог.

    Модель намеренно НЕ повторяет сырой объект провайдера. Здесь только
    metadata с понятной storage-семантикой, применимой к разным providers.
    Provider-specific поля (revision/resource_id/ETag/version и т.п.) сюда
    не входят и при необходимости проектируются отдельно.

    ``checksum``/``checksum_algorithm`` заполняются только если провайдер
    действительно отдаёт контрольную сумму с известным алгоритмом; иначе
    оба остаются ``None`` (не выдумываем checksum из ETag и подобного).
    """

    name: str
    path: str  # canonical POSIX, без префикса провайдера, напр. "/Regression/v.avi"
    kind: StorageItemKind

    size: Optional[int] = None
    modified_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    checksum: Optional[str] = None
    checksum_algorithm: Optional[str] = None

    mime_type: Optional[str] = None

    @property
    def is_dir(self) -> bool:
        return self.kind is StorageItemKind.DIRECTORY

    @property
    def is_file(self) -> bool:
        return self.kind is StorageItemKind.FILE
