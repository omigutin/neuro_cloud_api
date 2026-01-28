from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..sources.source_type import SourceType
else:
    from ..sources.source_type import SourceType


@dataclass(slots=True)
class NeuroCloudApiConfig:
    """
    Configuration for NeuroCloudApi
    
    Args:
        token: Токен для подключения к облачному сервису
        source_type: Тип сервиса (YANDEX_DISK | GOOGLE_DRIVE | S3)
        home_folder: Корневая папка, по умолчанию, например, MATLLER
        async_enabled: Использовать асинхронный источник (по умолчанию True)
    """
    token: str
    source_type: SourceType
    home_folder: str
    async_enabled: bool = True
