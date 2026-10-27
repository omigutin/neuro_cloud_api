# Документация библиотеки Neuro Cloud API

## Содержание

1. [Обзор](#обзор)
2. [Установка и настройка](#установка-и-настройка)
3. [Структура проекта](#структура-проекта)
4. [Контракт remote-путей](#контракт-remote-путей)
5. [Модель StorageItem](#модель-storageitem)
6. [Источники: BaseSource и BaseSourceAsync](#источники-basesource-и-basesourceasync)
7. [Фабрика, SourceType, конфигурация](#фабрика-sourcetype-конфигурация)
8. [Обработка ошибок](#обработка-ошибок)
9. [Примеры использования](#примеры-использования)
10. [Миграция с 1.0](#миграция-с-10)
11. [Производительность](#производительность)
12. [Расширение библиотеки](#расширение-библиотеки)

---

## Обзор

**Neuro Cloud API** — Python-библиотека с единым интерфейсом к облачным хранилищам. Сейчас реализован
Яндекс.Диск (синхронно и асинхронно); Google Drive и S3 — заглушки.

Принципы контракта:

- пути на удалённой стороне — канонические POSIX-пути от корня (`/Regression/v.avi`), без префиксов
  провайдера (`disk:`);
- метаданные возвращаются в provider-independent модели `StorageItem`, а не в сыром объекте провайдера;
- ошибки транслируются в собственную иерархию исключений с общим базовым `NeuroCloudError`;
- операции ничего не возвращают при успехе и бросают исключение при ошибке; перезапись — только явно
  (`overwrite=True`);
- синхронная (`BaseSource`) и асинхронная (`BaseSourceAsync`) версии ведут себя одинаково.

---

## Установка и настройка

### Требования

- Python 3.10+
- Poetry (или pip)

### Установка

```bash
poetry install            # зависимости библиотеки
poetry install --with dev # + pytest, mypy, black, flake8
```

Как зависимость другого проекта:

```bash
pip install "git+https://github.com/omigutin/neuro_cloud_api.git@main"
```

`yadisk` ставится с extras `sync-defaults` и `async-defaults` (requests для sync, httpx + aiofiles для
async) — без них клиенты `yadisk` не создаются.

### Переменные окружения для примеров и e2e-тестов

Файл `.env` в корне проекта:

```env
YADISK_TOKEN=your_yandex_disk_token_here
```

---

## Структура проекта

```
neuro_cloud_api/
├── src/neuro_cloud_api/
│   ├── __init__.py              # реэкспорт из api.py
│   ├── api.py                   # публичный API библиотеки
│   ├── errors.py                # иерархия исключений
│   ├── models.py                # StorageItem, StorageItemKind
│   ├── paths.py                 # контракт remote-путей
│   ├── settings/config.py       # NeuroCloudApiConfig
│   └── sources/
│       ├── base_source.py       # контракт sync-источника
│       ├── base_source_async.py # контракт async-источника
│       ├── _yadisk_common.py    # общее для sync/async Яндекс.Диска: пути, модель, ошибки
│       ├── yadisk_source.py
│       ├── yadisk_source_async.py
│       ├── ggldisk_source.py    # заглушка Google Drive
│       ├── s3_source.py         # заглушка S3
│       ├── source_factory.py
│       └── source_type.py
├── tests/
│   ├── unit/                    # без сети
│   ├── e2e/                     # live smoke против Яндекс.Диска (opt-in, нужен YADISK_TOKEN)
│   └── examples/                # примеры (запуск: run_sync.py / run_async.py)
└── docs/DOCUMENTATION.md
```

---

## Контракт remote-путей

Все публичные операции принимают и возвращают **канонические** пути (`neuro_cloud_api.paths`):

- путь абсолютный и начинается с `/`; корень — `/`;
- разделитель — `/`; обратный слэш `\` не принимается;
- префикс провайдера (`disk:/...`) не принимается на входе и не возвращается наружу;
- повторные `/`, сегменты `.` и `..` нормализуются; завершающий `/` убирается (кроме корня).

Некорректный путь → `ValueError`.

```python
from neuro_cloud_api.paths import normalize_remote_path, remote_parent, remote_name

normalize_remote_path("//a/./b/../c/")  # "/a/c"
remote_parent("/a/c")                   # "/a"
remote_name("/a/c")                     # "c"
```

---

## Модель StorageItem

`StorageItem` (frozen dataclass) — файл или каталог хранилища:

| Поле | Тип | Описание |
|---|---|---|
| `name` | `str` | имя последнего сегмента |
| `path` | `str` | канонический путь |
| `kind` | `StorageItemKind` | `FILE` или `DIRECTORY` |
| `size` | `Optional[int]` | размер в байтах |
| `modified_at`, `created_at` | `Optional[datetime]` | время изменения / создания |
| `checksum`, `checksum_algorithm` | `Optional[str]` | контрольная сумма и алгоритм (для Яндекс.Диска — md5 файлов); если провайдер её не отдаёт — оба `None` |
| `mime_type` | `Optional[str]` | MIME-тип |

Свойства `is_file` и `is_dir`. Provider-specific поля (revision, ETag и т.п.) в модель не входят.

---

## Источники: BaseSource и BaseSourceAsync

`BaseSource` — синхронный контракт, `BaseSourceAsync` — асинхронный (те же методы — корутины,
`iter_items` — async-генератор). Реализации: `YadiskSource`, `YadiskSourceAsync`.

### Жизненный цикл

| Метод | Поведение |
|---|---|
| `connect()` | проверяет доступ; ошибка → исключение (`CloudAuthenticationError`, `CloudConnectionError`, …) |
| `check_connection() -> bool` | health-check: `True`/`False`, **не бросает** |
| `disconnect()` | закрывает клиент; ошибка закрытия пишется в лог и не бросается |
| `with` / `async with` | `connect()` на входе, `disconnect()` на выходе |

Свойства: `token`, `source_type`, `is_connected`.

### Метаданные и обход

| Метод | Поведение |
|---|---|
| `exists(path) -> bool` | есть ли объект |
| `get_item(path) -> StorageItem` | метаданные; нет объекта → `RemoteNotFoundError` |
| `iter_items(path="/")` | ленивый обход содержимого каталога (не рекурсивно) |
| `list_items(path="/") -> list[StorageItem]` | то же, списком |

### Операции

| Метод | Поведение |
|---|---|
| `mkdir(path, *, parents=True, exist_ok=True)` | создать каталог; при `exist_ok=False` и существующем каталоге → `RemoteExistsError` |
| `upload_file(local_path, remote_path, *, overwrite=False, create_parents=True)` | загрузить файл; remote существует и `overwrite=False` → `RemoteExistsError`; нет локального файла → `LocalNotFoundError` |
| `download_file(remote_path, local_path, *, overwrite=False, create_parents=True)` | скачать файл; локальный файл существует и `overwrite=False` → `LocalExistsError` |
| `delete(path, *, recursive=False)` | удалить; непустой каталог без `recursive=True` → `RemoteConflictError` |
| `move(source, destination, *, overwrite=False)` | переместить; `destination` — полный целевой путь |
| `copy(source, destination, *, overwrite=False)` | скопировать; `destination` — полный целевой путь |

`create_parents=True` создаёт недостающие каталоги: на remote — при `upload_file`, локально — при
`download_file`.

### Устаревшие методы

`list_directories(path)` и `search_directories(name, path)` оставлены для совместимости, выдают
`DeprecationWarning` и будут удалены. Замена — `list_items` с фильтрацией:

```python
dirs = [item.path for item in source.list_items("/") if item.is_dir]
found = [item.path for item in source.list_items("/") if item.is_dir and "test" in item.name.lower()]
```

---

## Фабрика, SourceType, конфигурация

### SourceType

`YANDEX_DISK = "yandex_disk"`, `GOOGLE_DRIVE = "google_drive"` (не реализован), `S3 = "s3"`
(не реализован). `SourceType.from_string()` принимает `"yandex_disk"`, `"YANDEX_DISK"`, `"yandex-disk"`,
`"yandex disk"`; свойство `is_supported` — реализован ли тип.

### SourceFactory

```python
from neuro_cloud_api import NeuroCloudApiConfig, SourceFactory, SourceType

source = SourceFactory.create_source(token="...", source_type=SourceType.YANDEX_DISK)      # sync
source = SourceFactory.create_source(token="...", source_type="yandex_disk")                # из строки
source = SourceFactory.create_async_source(token="...", source_type=SourceType.YANDEX_DISK)

config = NeuroCloudApiConfig(token="...", source_type=SourceType.YANDEX_DISK, async_enabled=True)
source = SourceFactory.create_source_from_config(config)  # sync или async по async_enabled
```

`SourceFactory.parse()` приводит строку, `SourceType` или `NeuroCloudApiConfig` к `SourceType`. Для
Google Drive и S3 фабрика сразу бросает `SourceNotImplementedError`.

### NeuroCloudApiConfig

| Поле | Описание |
|---|---|
| `token: str` | токен облачного сервиса |
| `source_type: SourceType` | тип сервиса |
| `async_enabled: bool = True` | создавать асинхронный источник |
| `home_folder: Optional[str] = None` | **устарело**, не используется и не добавляется к путям; будет удалено |

---

## Обработка ошибок

Имена исключений не перекрывают встроенные исключения Python.

```
NeuroCloudError
├── CloudAuthenticationError     # неверный/протухший токен
├── CloudConnectionError         # транспорт: DNS, refused/reset, socket, timeout
├── CloudRateLimitError          # лимит запросов/трафика (HTTP 429 и аналоги)
├── RemoteNotFoundError          # remote-объект не найден
├── RemoteConflictError          # конфликт состояния remote
│   └── RemoteExistsError        # remote-объект уже существует
├── RemotePermissionError        # нет прав на remote
├── LocalFileError               # ошибка локальной ФС
│   ├── LocalNotFoundError       # нет локального источника (upload)
│   ├── LocalConflictError
│   │   └── LocalExistsError     # локальный destination существует (download)
│   └── LocalPermissionError     # нет прав локально
├── ProviderError                # 5xx и прочие неклассифицированные ошибки провайдера
└── SourceNotImplementedError    # источник ещё не реализован (также NotImplementedError)
```

Исходное исключение провайдера доступно через `__cause__`.

```python
from neuro_cloud_api import (
    CloudAuthenticationError, CloudConnectionError, NeuroCloudError, RemoteExistsError, YadiskSource,
)

try:
    with YadiskSource(token="...") as source:
        source.upload_file("file.txt", "/backup/file.txt")
except CloudAuthenticationError:
    print("Неверный токен")
except RemoteExistsError:
    print("Файл уже есть; для перезаписи — overwrite=True")
except CloudConnectionError as e:
    print(f"Сеть недоступна: {e}")
except NeuroCloudError as e:
    print(f"Ошибка хранилища: {e}")
```

---

## Примеры использования

### Синхронно

```python
import os
from pathlib import Path

from neuro_cloud_api import YadiskSource

with YadiskSource(token=os.environ["YADISK_TOKEN"]) as source:
    for item in source.list_items("/"):
        print(item.kind.value, item.path, item.size)
    source.upload_file("report.xlsx", "/Reports/2026/report.xlsx", overwrite=True)
    source.download_file("/Reports/2026/report.xlsx", Path("downloads/report.xlsx"), overwrite=True)
    source.move("/Reports/2026/report.xlsx", "/Archive/report.xlsx")
```

### Асинхронно, параллельная загрузка

```python
import asyncio
import os
from pathlib import Path

from neuro_cloud_api import YadiskSourceAsync


async def main() -> None:
    files = sorted(Path("videos").glob("*.mp4"))
    async with YadiskSourceAsync(token=os.environ["YADISK_TOKEN"]) as source:
        await source.mkdir("/Videos")
        await asyncio.gather(*(source.upload_file(f, f"/Videos/{f.name}", overwrite=True) for f in files))
        async for item in source.iter_items("/Videos"):
            print(item.name, item.checksum)


asyncio.run(main())
```

### Готовые примеры

```bash
poetry run python run_sync.py   # последовательная загрузка/скачивание 15 файлов
poetry run python run_async.py  # то же параллельно
```

Точки входа импортируют функции из `tests/examples/example_sync.py` и `tests/examples/example_async.py`.

---

## Миграция с 1.0

| Было (1.0) | Стало (0.2) |
|---|---|
| `NeuroCloudAPIError` | `NeuroCloudError` |
| `AuthenticationError` | `CloudAuthenticationError` |
| `ConnectionError` | `CloudConnectionError` (только сеть) или конкретный класс |
| `FileNotFoundError` | `RemoteNotFoundError` / `LocalNotFoundError` |
| `UploadError`, `DownloadError` | конкретные классы иерархии; общий — `NeuroCloudError` |
| `connect() -> bool` | `connect() -> None`, ошибка — исключение |
| `check_connection()` бросал исключения | возвращает `True`/`False`, не бросает |
| `upload_file`/`download_file` `-> bool`, молча перезаписывали | `-> None`, перезапись только при `overwrite=True` |
| пути вида `disk:/Folder` | канонические `/Folder` |
| `list_directories`, `search_directories` | `list_items` / `iter_items` (старые — deprecated) |
| `NeuroCloudApiConfig.home_folder` обязателен | необязателен и не используется |
| импорт `from src.neuro_cloud_api import ...` | `from neuro_cloud_api import ...` |

Версия понижена до 0.2.0: публичный API ещё может меняться.

---

## Производительность

Замеры примеров (`run_sync.py` / `run_async.py`), 15 файлов по 1 MB:

| Операция | Sync (последовательно) | Async (параллельно) |
|---|---|---|
| Загрузка 15 файлов | ~6.0–8.0 сек | ~2.5–4.0 сек |
| Скачивание 15 файлов | ~6.5–9.0 сек | ~2.8–4.5 сек |

Одиночные операции (список каталога, загрузка/скачивание одного файла) в обеих версиях занимают
~0.4–1 сек. Async выигрывает только на множестве параллельных операций. Результаты зависят от сети и
нагрузки на сервер.

---

## Расширение библиотеки

1. Унаследуйте `BaseSource` (и/или `BaseSourceAsync`) и реализуйте все абстрактные методы контракта:
   `connect`, `disconnect`, `check_connection`, `exists`, `get_item`, `iter_items`, `mkdir`,
   `upload_file`, `download_file`, `delete`, `move`, `copy`.
2. Нормализуйте входные пути через `normalize_remote_path`, отдавайте наружу канонические пути и
   `StorageItem`, транслируйте ошибки провайдера в иерархию `errors.py`. Общую для sync и async логику
   держите в одном модуле (как `_yadisk_common.py`).
3. Добавьте значение в `SourceType` и ветку в `SourceFactory`.
4. Покройте трансляцию ошибок и маппинг модели юнит-тестами (см. `tests/unit/test_yadisk_common.py`).

---

## Тесты

```bash
poetry run pytest                       # юнит-тесты; e2e пропускаются без токена
$env:YADISK_TOKEN = "<token>"; poetry run pytest tests/e2e -v   # live smoke (PowerShell)
```

e2e работает только внутри `/NeuroCloudApiTests` на Диске и удаляет за собой созданное.
