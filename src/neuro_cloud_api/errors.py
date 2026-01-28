"""Базовые исключения для Neuro Cloud API."""


class NeuroCloudAPIError(Exception):
    """Базовое исключение для всех ошибок Neuro Cloud API."""

    def __init__(self, message: str, *args):
        super().__init__(message, *args)
        self.message = message


class ConnectionError(NeuroCloudAPIError):
    """Ошибка подключения к облачному хранилищу."""

    pass


class AuthenticationError(NeuroCloudAPIError):
    """Ошибка аутентификации (неверный токен)."""

    pass


class FileNotFoundError(NeuroCloudAPIError):
    """Файл не найден в облачном хранилище."""

    pass


class UploadError(NeuroCloudAPIError):
    """Ошибка загрузки файла."""

    pass


class DownloadError(NeuroCloudAPIError):
    """Ошибка скачивания файла."""

    pass


class SourceNotImplementedError(NeuroCloudAPIError, NotImplementedError):
    """Источник еще не реализован."""

    pass
