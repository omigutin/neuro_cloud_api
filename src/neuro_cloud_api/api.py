"""Публичный API библиотеки Neuro Cloud API."""

# Доменная модель
from .models import StorageItem, StorageItemKind

# Исключения
from .errors import (
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
    LocalConflictError,
    LocalExistsError,
    LocalPermissionError,
    ProviderError,
    SourceNotImplementedError,
)

# Интерфейсы
from .sources.base_source import BaseSource
from .sources.base_source_async import BaseSourceAsync

# Реализации
from .sources.yadisk_source import YadiskSource
from .sources.yadisk_source_async import YadiskSourceAsync

# Factory и типы
from .sources.source_factory import SourceFactory
from .sources.source_type import SourceType

# Конфигурация
from .settings.config import NeuroCloudApiConfig

__all__ = [
    # Модель
    "StorageItem",
    "StorageItemKind",
    # Исключения
    "NeuroCloudError",
    "CloudAuthenticationError",
    "CloudConnectionError",
    "CloudRateLimitError",
    "RemoteNotFoundError",
    "RemoteConflictError",
    "RemoteExistsError",
    "RemotePermissionError",
    "LocalFileError",
    "LocalNotFoundError",
    "LocalConflictError",
    "LocalExistsError",
    "LocalPermissionError",
    "ProviderError",
    "SourceNotImplementedError",
    # Интерфейсы
    "BaseSource",
    "BaseSourceAsync",
    # Реализации
    "YadiskSource",
    "YadiskSourceAsync",
    # Factory и типы
    "SourceFactory",
    "SourceType",
    # Конфигурация
    "NeuroCloudApiConfig",
]
