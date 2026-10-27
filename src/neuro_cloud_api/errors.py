"""Иерархия исключений Neuro Cloud API.

Публичные имена намеренно не затеняют встроенные исключения Python
(``ConnectionError``, ``FileNotFoundError`` и т.п.). Consumer может различать
причину ошибки, ловя нужный класс или общий базовый ``NeuroCloudError``.

Иерархия::

    NeuroCloudError
    ├── CloudAuthenticationError     # неверный/протухший токен
    ├── CloudConnectionError         # только transport: DNS, refused/reset, socket, timeout
    ├── CloudRateLimitError          # rate limit (HTTP 429 и лимиты трафика)
    ├── RemoteNotFoundError          # remote-объект не найден
    ├── RemoteConflictError          # конфликт состояния remote
    │   └── RemoteExistsError        # remote-объект уже существует (overwrite=False)
    ├── RemotePermissionError        # нет прав на remote
    ├── LocalFileError               # ошибка локальной ФС
    │   ├── LocalNotFoundError       # локальный источник отсутствует (upload)
    │   ├── LocalConflictError
    │   │   └── LocalExistsError     # локальный destination существует (download, overwrite=False)
    │   └── LocalPermissionError     # нет прав локально
    ├── ProviderError                # 5xx и прочие неклассифицированные ошибки провайдера
    └── SourceNotImplementedError    # источник ещё не реализован
"""

__all__ = [
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
]


class NeuroCloudError(Exception):
    """Базовое исключение для всех ошибок Neuro Cloud API."""

    def __init__(self, message: str = "", *args):
        super().__init__(message, *args)
        self.message = message


# ── Ошибки уровня облачного провайдера ──────────────────────────────────────

class CloudAuthenticationError(NeuroCloudError):
    """Ошибка аутентификации (неверный или протухший токен)."""


class CloudConnectionError(NeuroCloudError):
    """Проблема транспорта/сети: DNS, connection refused/reset, socket, timeout."""


class CloudRateLimitError(NeuroCloudError):
    """Превышен лимит запросов/трафика (HTTP 429 и аналоги)."""


class RemoteNotFoundError(NeuroCloudError):
    """Remote-объект не найден."""


class RemoteConflictError(NeuroCloudError):
    """Конфликт состояния remote (нет родителя, ресурс заблокирован, каталог не пуст)."""


class RemoteExistsError(RemoteConflictError):
    """Remote-объект уже существует (например, при ``overwrite=False``)."""


class RemotePermissionError(NeuroCloudError):
    """Недостаточно прав для операции над remote-объектом."""


# ── Ошибки локальной файловой системы ───────────────────────────────────────

class LocalFileError(NeuroCloudError):
    """Ошибка локальной файловой системы."""


class LocalNotFoundError(LocalFileError):
    """Локальный источник не найден (например, при upload)."""


class LocalConflictError(LocalFileError):
    """Конфликт состояния локальной ФС."""


class LocalExistsError(LocalConflictError):
    """Локальный destination уже существует (например, download при ``overwrite=False``)."""


class LocalPermissionError(LocalFileError):
    """Недостаточно прав в локальной файловой системе."""


# ── Прочее ──────────────────────────────────────────────────────────────────

class ProviderError(NeuroCloudError):
    """Неклассифицированная ошибка провайдера (5xx, некорректный ответ и т.п.)."""


class SourceNotImplementedError(NeuroCloudError, NotImplementedError):
    """Источник ещё не реализован."""
