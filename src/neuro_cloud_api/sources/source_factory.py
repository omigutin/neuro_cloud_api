from typing import Optional, Union

from .base_source import BaseSource
from .base_source_async import BaseSourceAsync
from .source_type import SourceType
from .yadisk_source import YadiskSource
from .yadisk_source_async import YadiskSourceAsync
from ..settings.config import NeuroCloudApiConfig
from ..errors import SourceNotImplementedError


class SourceFactory:
    """
    Фабрика для создания источников облачных хранилищ.
    Реализует паттерн Factory для автоматического выбора и создания
    соответствующего источника на основе типа.
    """

    @staticmethod
    def parse(source_type: Union[str, SourceType, NeuroCloudApiConfig]) -> SourceType:
        """
        Определяет тип источника из различных входных данных.

        Args:
            source_type: Может быть:
                - строкой ("yandex_disk", "google_drive", "s3")
                - SourceType enum
                - NeuroCloudApiConfig объект

        Returns:
            SourceType enum

        Raises:
            ValueError: Если тип источника не может быть определен
        """
        if isinstance(source_type, SourceType):
            return source_type
        elif isinstance(source_type, NeuroCloudApiConfig):
            return source_type.source_type
        elif isinstance(source_type, str):
            return SourceType.from_string(source_type)
        else:
            raise ValueError(f"Неподдерживаемый тип аргумента: {type(source_type)}")

    @staticmethod
    def create_source(
        token: Optional[str] = None,
        source_type: Optional[Union[str, SourceType, NeuroCloudApiConfig]] = None,
        config: Optional[NeuroCloudApiConfig] = None
    ) -> BaseSource:
        """
        Создает синхронный источник облачного хранилища на основе типа.

        Args:
            token: Токен для авторизации (опционально, если передан config)
            source_type: Тип источника (строка, SourceType или NeuroCloudApiConfig)
            config: Конфигурация (если передан, source_type и token игнорируются)

        Returns:
            Экземпляр соответствующего источника (BaseSource)

        Raises:
            ValueError: Если тип источника не поддерживается
            SourceNotImplementedError: Если источник еще не реализован
        """
        # Если передан config, используем его
        if config is not None:
            source_type_enum = config.source_type
            token = config.token
        elif source_type is not None:
            source_type_enum = SourceFactory.parse(source_type)
            if token is None:
                raise ValueError("Необходимо указать token или передать config")
        else:
            raise ValueError("Необходимо указать source_type или config")

        # Создаем соответствующий источник на основе типа
        if source_type_enum == SourceType.YANDEX_DISK:
            return YadiskSource(token=token)
        elif source_type_enum == SourceType.GOOGLE_DRIVE:
            # Проверяем, существует ли реализация
            try:
                from .ggldisk_source import GoogleDriveSource
                return GoogleDriveSource(token=token)
            except ImportError:
                raise SourceNotImplementedError("Google Drive источник еще не реализован")
        elif source_type_enum == SourceType.S3:
            # Проверяем, существует ли реализация
            try:
                from .s3_source import S3Source
                return S3Source(token=token)
            except ImportError:
                raise SourceNotImplementedError("S3 источник еще не реализован")
        else:
            raise ValueError(f"Неподдерживаемый тип источника: {source_type_enum}")

    @staticmethod
    def create_async_source(
        token: Optional[str] = None,
        source_type: Optional[Union[str, SourceType, NeuroCloudApiConfig]] = None,
        config: Optional[NeuroCloudApiConfig] = None
    ) -> BaseSourceAsync:
        """
        Создает асинхронный источник облачного хранилища на основе типа.

        Args:
            token: Токен для авторизации (опционально, если передан config)
            source_type: Тип источника (строка, SourceType или NeuroCloudApiConfig)
            config: Конфигурация (если передан, source_type и token игнорируются)

        Returns:
            Экземпляр соответствующего асинхронного источника (BaseSourceAsync)

        Raises:
            ValueError: Если тип источника не поддерживается
            SourceNotImplementedError: Если источник еще не реализован
        """
        # Если передан config, используем его
        if config is not None:
            source_type_enum = config.source_type
            token = config.token
        elif source_type is not None:
            source_type_enum = SourceFactory.parse(source_type)
            if token is None:
                raise ValueError("Необходимо указать token или передать config")
        else:
            raise ValueError("Необходимо указать source_type или config")

        # Создаем соответствующий асинхронный источник на основе типа
        if source_type_enum == SourceType.YANDEX_DISK:
            return YadiskSourceAsync(token=token)
        elif source_type_enum == SourceType.GOOGLE_DRIVE:
            # Проверяем, существует ли реализация
            try:
                from .ggldisk_source import GoogleDriveSource
                # Если есть только sync версия, создаем её, но это не async
                raise SourceNotImplementedError("Google Drive асинхронный источник еще не реализован")
            except ImportError:
                raise SourceNotImplementedError("Google Drive асинхронный источник еще не реализован")
        elif source_type_enum == SourceType.S3:
            # Проверяем, существует ли реализация
            try:
                from .s3_source import S3Source
                # Если есть только sync версия, создаем её, но это не async
                raise SourceNotImplementedError("S3 асинхронный источник еще не реализован")
            except ImportError:
                raise SourceNotImplementedError("S3 асинхронный источник еще не реализован")
        else:
            raise ValueError(f"Неподдерживаемый тип источника: {source_type_enum}")

    @staticmethod
    def create_source_from_config(config: NeuroCloudApiConfig) -> Union[BaseSource, BaseSourceAsync]:
        """
        Создает источник на основе конфигурации.
        Автоматически выбирает синхронный или асинхронный источник
        в зависимости от параметра async_enabled в конфиге.

        Args:
            config: Конфигурация NeuroCloudApiConfig

        Returns:
            Экземпляр соответствующего источника (BaseSource или BaseSourceAsync)
        """
        if config.async_enabled:
            return SourceFactory.create_async_source(config=config)
        else:
            return SourceFactory.create_source(config=config)
