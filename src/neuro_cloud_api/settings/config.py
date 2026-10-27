from dataclasses import dataclass
from typing import Optional

from ..sources.source_type import SourceType


@dataclass(slots=True)
class NeuroCloudApiConfig:
    """Конфигурация NeuroCloudApi.

    Args:
        token: Токен для подключения к облачному сервису.
        source_type: Тип сервиса (YANDEX_DISK | GOOGLE_DRIVE | S3).
        home_folder: DEPRECATED. Не используется и НЕ добавляется скрытым
            префиксом к путям. Оставлено опциональным для обратной
            совместимости; будет удалено. Все публичные методы работают с
            явными canonical remote paths.
        async_enabled: Использовать асинхронный источник (по умолчанию True).
    """

    token: str
    source_type: SourceType
    home_folder: Optional[str] = None
    async_enabled: bool = True
