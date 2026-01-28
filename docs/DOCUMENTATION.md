# Документация библиотеки Neuro Cloud API

## Содержание

1. [Обзор](#обзор)
2. [Архитектура](#архитектура)
3. [Установка и настройка](#установка-и-настройка)
4. [Структура проекта](#структура-проекта)
5. [Основные компоненты](#основные-компоненты)
6. [API Reference](#api-reference)
7. [Примеры использования](#примеры-использования)
8. [Паттерны проектирования](#паттерны-проектирования)
9. [Производительность](#производительность)

---

## Обзор

**Neuro Cloud API** — это Python-библиотека для работы с облачными хранилищами данных. Библиотека предоставляет единый интерфейс для работы с различными облачными сервисами (Яндекс.Диск, Google Drive, S3) и поддерживает как синхронные, так и асинхронные операции.

### Основные возможности

- ✅ Работа с Яндекс.Диском (синхронно и асинхронно)
- ✅ Единый интерфейс для различных облачных хранилищ
- ✅ Паттерн Factory для автоматического выбора источника
- ✅ Загрузка и скачивание файлов
- ✅ Поиск директорий по имени
- ✅ Получение списка директорий
- ✅ Замер производительности операций
- ✅ Поддержка конфигурации через dataclass

---

## Архитектура

Библиотека построена на принципах объектно-ориентированного программирования с использованием следующих паттернов:

- **Abstract Factory** — базовый абстрактный класс `BaseSource`
- **Factory Pattern** — класс `SourceFactory` для создания источников
- **Strategy Pattern** — различные реализации для разных облачных сервисов

### Диаграмма классов

```
BaseSource (ABC) - синхронный интерфейс
    ├── YadiskSource (синхронный)
    ├── GoogleDriveSource (заглушка)
    └── S3Source (заглушка)

BaseSourceAsync (ABC) - асинхронный интерфейс
    └── YadiskSourceAsync (асинхронный)

SourceFactory
    ├── parse()
    ├── create_source() -> BaseSource
    ├── create_async_source() -> BaseSourceAsync
    └── create_source_from_config() -> Union[BaseSource, BaseSourceAsync]

SourceType (Enum)
    ├── YANDEX_DISK
    ├── GOOGLE_DRIVE
    └── S3

NeuroCloudApiConfig (dataclass, slots=True)
```

**Важно:** Синхронные и асинхронные интерфейсы разделены на `BaseSource` и `BaseSourceAsync`. Это обеспечивает четкое разделение контрактов и предотвращает смешивание sync и async методов.

---

## Установка и настройка

### Требования

- Python 3.9+
- Poetry (для управления зависимостями) или pip

### Установка через Poetry (рекомендуется)

1. Установите Poetry, если еще не установлен:

```bash
# Linux/macOS
curl -sSL https://install.python-poetry.org | python3 -

# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

2. Установите зависимости:

```bash
poetry install
```

3. Активируйте виртуальное окружение:

```bash
poetry shell
```

Или запускайте команды через Poetry:

```bash
poetry run python run_sync.py
```

### Установка через pip

```bash
pip install yadisk python-dotenv
```

**Примечание:** `httpx` устанавливается автоматически с `yadisk` для асинхронных операций.

### Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
YADISK_TOKEN=your_yandex_disk_token_here
```

---

## Структура проекта

```
yadisk_api/
├── src/
│   └── neuro_cloud_api/
│       ├── __init__.py                 # Тонкий реэкспорт из api.py
│       ├── api.py                       # Публичный API контракт библиотеки
│       ├── errors.py                    # Публичные исключения
│       ├── sources/
│       │   ├── __init__.py
│       │   ├── base_source.py          # Базовый абстрактный класс (sync)
│       │   ├── base_source_async.py    # Базовый абстрактный класс (async)
│       │   ├── yadisk_source.py        # Синхронная реализация для Яндекс.Диска
│       │   ├── yadisk_source_async.py  # Асинхронная реализация для Яндекс.Диска
│       │   ├── source_factory.py       # Фабрика для создания источников
│       │   ├── source_type.py          # Enum типов источников
│       │   ├── ggldisk_source.py       # Заглушка для Google Drive
│       │   └── s3_source.py            # Заглушка для S3
│       └── settings/
│           └── config.py               # Конфигурация NeuroCloudApiConfig
├── tests/
│   ├── unit/                           # Юнит-тесты
│   ├── integration/                    # Интеграционные тесты
│   ├── e2e/                            # End-to-end тесты
│   └── examples/
│       ├── example_sync.py              # Функция синхронного примера
│       └── example_async.py             # Функция асинхронного примера
├── run_sync.py                          # Точка входа для синхронного примера
├── run_async.py                         # Точка входа для асинхронного примера
├── docs/
│   └── DOCUMENTATION.md                 # Полная документация
├── pyproject.toml                      # Конфигурация Poetry
├── poetry.lock                         # Файл блокировки зависимостей (генерируется автоматически)
├── README.md                           # Краткое описание и инструкции
└── LICENSE                             # Лицензия
```

---

## Основные компоненты

### 1. BaseSource (Базовый абстрактный класс для синхронных операций)

**Файл:** `src/neuro_cloud_api/sources/base_source.py`

Абстрактный базовый класс, определяющий синхронный интерфейс для всех источников облачных хранилищ.

#### Атрибуты (приватные, доступ через @property)

- `_token: str` — токен для авторизации (доступ через `token` property)
- `_source_type: SourceType` — тип источника (доступ через `source_type` property)
- `_client: Optional[Any]` — клиент облачного хранилища (приватный)
- `_is_connected: bool` — статус подключения (доступ через `is_connected` property)

#### Properties

- `token: str` — возвращает токен для авторизации
- `source_type: SourceType` — возвращает тип источника
- `is_connected: bool` — возвращает статус подключения

#### Абстрактные методы

Все подклассы должны реализовать:

- `connect() -> bool` — подключение к облачному хранилищу
- `check_connection() -> bool` — проверка подключения
- `list_directories(path: str = "/") -> List[str]` — получение списка директорий
- `download_file(remote_path: str, local_path: Union[str, Path]) -> bool` — скачивание файла
- `upload_file(local_path: Union[str, Path], remote_path: str) -> bool` — загрузка файла
- `search_directories(name: str, path: str = "/") -> List[str]` — поиск директорий

#### Методы

- `disconnect()` — отключение от облачного хранилища

---

### 2. YadiskSource (Синхронная реализация)

**Файл:** `src/neuro_cloud_api/sources/yadisk_source.py`

Синхронная реализация для работы с Яндекс.Диском.

#### Инициализация

```python
source = YadiskSource(token="your_token")
```

#### Методы

##### `connect() -> bool`
Подключается к Яндекс.Диску и проверяет валидность токена.

##### `check_connection() -> bool`
Проверяет валидность токена без установки соединения.

##### `list_directories(path: str = "/") -> List[str]`
Возвращает список всех директорий в указанном пути.

**Пример:**
```python
dirs = source.list_directories("/")
# Возвращает: ['disk:/Folder1', 'disk:/Folder2', ...]
```

##### `search_directories(name: str, path: str = "/") -> List[str]`
Ищет директории, содержащие указанное имя (регистронезависимый поиск).

**Пример:**
```python
found = source.search_directories("test", "/")
# Найдет все директории с "test" в имени
```

##### `download_file(remote_path: str, local_path: Union[str, Path]) -> bool`
Скачивает файл с Яндекс.Диска на локальный диск.

**Пример:**
```python
source.download_file(
    remote_path="/test_upload.txt",
    local_path=Path("downloads/test_upload.txt")
)
```

##### `upload_file(local_path: Union[str, Path], remote_path: str) -> bool`
Загружает файл на Яндекс.Диск.

**Особенности:**
- Автоматически создает необходимые директории на диске
- Проверяет существование локального файла

**Пример:**
```python
source.upload_file(
    local_path="test_upload.txt",
    remote_path="/test_upload.txt"
)
```

##### `_ensure_directory_exists(remote_path: str) -> None`
Приватный метод для рекурсивного создания директорий на Яндекс.Диске.

---

### 3. BaseSourceAsync (Базовый абстрактный класс для асинхронных операций)

**Файл:** `src/neuro_cloud_api/sources/base_source_async.py`

Абстрактный базовый класс, определяющий асинхронный интерфейс для всех источников облачных хранилищ. Все методы являются асинхронными и должны вызываться с `await`.

#### Атрибуты (приватные, доступ через @property)

Аналогично `BaseSource`, но все методы асинхронные.

---

### 4. YadiskSourceAsync (Асинхронная реализация)

**Файл:** `src/neuro_cloud_api/sources/yadisk_source_async.py`

Асинхронная реализация для работы с Яндекс.Диском. Наследуется от `BaseSourceAsync`, все методы являются асинхронными и должны вызываться с `await`.

#### Инициализация

```python
source = YadiskSourceAsync(token="your_token")
```

#### Методы

Все методы аналогичны синхронной версии, но являются асинхронными:

- `async def connect() -> bool`
- `async def check_connection() -> bool`
- `async def list_directories(path: str = "/") -> List[str]`
- `async def search_directories(name: str, path: str = "/") -> List[str]`
- `async def download_file(...) -> bool`
- `async def upload_file(...) -> bool`
- `async def disconnect()`

#### Особенности асинхронной версии

1. **Производительность** — асинхронная версия может быть быстрее при работе с множественными операциями благодаря параллельной обработке.

2. **Неблокирующие операции** — все операции не блокируют выполнение программы, что позволяет обрабатывать другие задачи во время ожидания ответа от API.

**Пример использования:**
```python
import asyncio

async def main():
    source = YadiskSourceAsync(token="your_token")
    await source.connect()
    dirs = await source.list_directories("/")
    await source.disconnect()

asyncio.run(main())
```

---

### 5. SourceFactory (Фабрика источников)

**Файл:** `src/neuro_cloud_api/sources/source_factory.py`

Реализует паттерн Factory для автоматического создания источников на основе типа.

#### Методы

##### `parse(source_type: Union[str, SourceType, NeuroCloudApiConfig]) -> SourceType`

Определяет тип источника из различных входных данных.

**Параметры:**
- `source_type` — может быть:
  - строкой: `"yandex_disk"`, `"google_drive"`, `"s3"`
  - `SourceType` enum
  - `NeuroCloudApiConfig` объект

**Возвращает:** `SourceType` enum

**Примеры:**
```python
# Из строки
source_type = SourceFactory.parse("yandex_disk")

# Из enum
source_type = SourceFactory.parse(SourceType.YANDEX_DISK)

# Из конфига
config = NeuroCloudApiConfig(...)
source_type = SourceFactory.parse(config)
```

##### `create_source(token: Optional[str] = None, source_type: Optional[Union[str, SourceType, NeuroCloudApiConfig]] = None, config: Optional[NeuroCloudApiConfig] = None) -> BaseSource`

Создает синхронный источник облачного хранилища.

**Параметры:**
- `token` — токен для авторизации (опционально, если передан `config`)
- `source_type` — тип источника (строка, SourceType или NeuroCloudApiConfig)
- `config` — конфигурация (если передан, `source_type` и `token` игнорируются)

**Возвращает:** Экземпляр соответствующего источника (BaseSource)

**Примеры:**
```python
# Через token и SourceType
source = SourceFactory.create_source(
    token="your_token",
    source_type=SourceType.YANDEX_DISK
)

# Через строку
source = SourceFactory.create_source(
    token="your_token",
    source_type="yandex_disk"
)

# Через конфиг
config = NeuroCloudApiConfig(
    token="your_token",
    source_type=SourceType.YANDEX_DISK,
    home_folder="/",
    async_enabled=False
)
source = SourceFactory.create_source(config=config)
```

##### `create_async_source(...) -> BaseSourceAsync`

Аналогично `create_source()`, но создает асинхронный источник.

**Возвращает:** Экземпляр соответствующего асинхронного источника (BaseSourceAsync)

**Примеры:**
```python
# Через token и SourceType
source = SourceFactory.create_async_source(
    token="your_token",
    source_type=SourceType.YANDEX_DISK
)

# Через строку
source = SourceFactory.create_async_source(
    token="your_token",
    source_type="yandex_disk"
)
```

##### `create_source_from_config(config: NeuroCloudApiConfig) -> Union[BaseSource, BaseSourceAsync]`

Создает источник на основе конфигурации. Автоматически выбирает синхронный или асинхронный источник в зависимости от параметра `async_enabled` в конфиге.

**Возвращает:** Экземпляр соответствующего источника (BaseSource или BaseSourceAsync)

**Пример:**
```python
config = NeuroCloudApiConfig(
    token="your_token",
    source_type=SourceType.YANDEX_DISK,
    home_folder="/",
    async_enabled=True  # Создаст YadiskSourceAsync
)
source = SourceFactory.create_source_from_config(config)
```

---

### 6. SourceType (Enum типов источников)

**Файл:** `src/neuro_cloud_api/sources/source_type.py`

Перечисление типов облачных хранилищ.

#### Значения

- `YANDEX_DISK = "yandex_disk"` — Яндекс.Диск
- `GOOGLE_DRIVE = "google_drive"` — Google Drive (не реализован)
- `S3 = "s3"` — Amazon S3 (не реализован)

#### Методы

##### `from_string(value: str) -> SourceType`

Преобразует строку в `SourceType`. Поддерживает различные форматы:
- `"yandex_disk"`, `"YANDEX_DISK"`, `"yandex-disk"`, `"yandex disk"`

**Пример:**
```python
source_type = SourceType.from_string("yandex_disk")
```

##### `is_supported` (property)

Проверяет, поддерживается ли тип источника.

**Пример:**
```python
if SourceType.YANDEX_DISK.is_supported:
    print("Поддерживается")
```

---

### 7. NeuroCloudApiConfig (Конфигурация)

**Файл:** `src/neuro_cloud_api/settings/config.py`

Dataclass для хранения конфигурации библиотеки. Использует `slots=True` для оптимизации памяти.

#### Поля

- `token: str` — токен для подключения к облачному сервису
- `source_type: SourceType` — тип сервиса (SourceType enum, не общий Enum)
- `home_folder: str` — корневая папка по умолчанию (например, "MATLLER")
- `async_enabled: bool = True` — использовать асинхронный источник

#### Пример

```python
from src.neuro_cloud_api.settings.config import NeuroCloudApiConfig
from src.neuro_cloud_api.sources.source_type import SourceType

config = NeuroCloudApiConfig(
    token="your_token",
    source_type=SourceType.YANDEX_DISK,
    home_folder="/MATLLER",
    async_enabled=True
)
```

---

## API Reference

### Импорт основных классов

Все публичные классы, интерфейсы и исключения экспортируются через `api.py` и доступны через главный пакет:

```python
from src.neuro_cloud_api import (
    # Интерфейсы
    BaseSource,
    BaseSourceAsync,
    # Реализации
    YadiskSource,
    YadiskSourceAsync,
    # Factory и типы
    SourceFactory,
    SourceType,
    # Конфигурация
    NeuroCloudApiConfig,
    # Исключения
    NeuroCloudAPIError,
    ConnectionError,
    AuthenticationError,
    FileNotFoundError,
    UploadError,
    DownloadError,
    SourceNotImplementedError,
)
```

### Полный список методов BaseSource

| Метод | Синхронный | Асинхронный | Описание |
|-------|-----------|-------------|----------|
| `connect()` | ✅ | ✅ | Подключение к хранилищу |
| `check_connection()` | ✅ | ✅ | Проверка подключения |
| `list_directories(path)` | ✅ | ✅ | Список директорий |
| `search_directories(name, path)` | ✅ | ✅ | Поиск директорий |
| `download_file(remote, local)` | ✅ | ✅ | Скачивание файла |
| `upload_file(local, remote)` | ✅ | ✅ | Загрузка файла |
| `disconnect()` | ✅ | ✅ | Отключение |

---

## Примеры использования

### Пример 1: Базовое использование (синхронно)

```python
import os
from pathlib import Path
from dotenv import load_dotenv
from src.neuro_cloud_api import YadiskSource

load_dotenv()
token = os.getenv('YADISK_TOKEN')

# Создание источника
source = YadiskSource(token=token)

# Подключение
if source.connect():
    # Список директорий
    dirs = source.list_directories("/")
    print(f"Найдено директорий: {len(dirs)}")
    
    # Поиск директорий
    found = source.search_directories("test", "/")
    
    # Загрузка файла
    source.upload_file("local_file.txt", "/remote_file.txt")
    
    # Скачивание файла
    source.download_file("/remote_file.txt", Path("downloads/local_file.txt"))
    
    # Отключение
    source.disconnect()
```

### Пример 2: Асинхронное использование

```python
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from src.neuro_cloud_api import YadiskSourceAsync

load_dotenv()
token = os.getenv('YADISK_TOKEN')

async def main():
    source = YadiskSourceAsync(token=token)
    
    if await source.connect():
        # Асинхронные операции
        dirs = await source.list_directories("/")
        found = await source.search_directories("test", "/")
        
        await source.upload_file("local_file.txt", "/remote_file.txt")
        await source.download_file("/remote_file.txt", Path("downloads/local_file.txt"))
        
        await source.disconnect()

asyncio.run(main())
```

### Пример 3: Использование Factory

```python
import os
from dotenv import load_dotenv
from src.neuro_cloud_api import SourceFactory, SourceType

load_dotenv()
token = os.getenv('YADISK_TOKEN')

# Создание через Factory
source = SourceFactory.create_source(
    token=token,
    source_type=SourceType.YANDEX_DISK
)

# Или через строку
source = SourceFactory.create_source(
    token=token,
    source_type="yandex_disk"
)

# Или через конфиг
from src.neuro_cloud_api.settings.config import NeuroCloudApiConfig

config = NeuroCloudApiConfig(
    token=token,
    source_type=SourceType.YANDEX_DISK,
    home_folder="/",
    async_enabled=False
)
source = SourceFactory.create_source_from_config(config)
```

### Пример 4: Загрузка и скачивание множества файлов

#### Синхронная версия (последовательно)

```python
import os
from pathlib import Path
from dotenv import load_dotenv
from src.neuro_cloud_api import YadiskSource

load_dotenv()
source = YadiskSource(token=os.getenv('YADISK_TOKEN'))
source.connect()

# Список файлов для загрузки
files_to_upload = [
    Path("video1.mp4"),
    Path("video2.mp4"),
    # ... еще файлы
]

# Последовательная загрузка
for local_file in files_to_upload:
    remote_path = f"/videos/{local_file.name}"
    source.upload_file(local_path=local_file, remote_path=remote_path)

# Последовательное скачивание
for local_file in files_to_upload:
    remote_path = f"/videos/{local_file.name}"
    download_path = Path("downloads") / local_file.name
    source.download_file(remote_path=remote_path, local_path=download_path)

source.disconnect()
```

#### Асинхронная версия (параллельно)

```python
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from src.neuro_cloud_api import YadiskSourceAsync

load_dotenv()

async def main():
    source = YadiskSourceAsync(token=os.getenv('YADISK_TOKEN'))
    await source.connect()
    
    # Список файлов для загрузки
    files_to_upload = [
        Path("video1.mp4"),
        Path("video2.mp4"),
        # ... еще файлы
    ]
    
    # Параллельная загрузка
    upload_tasks = [
        source.upload_file(
            local_path=file,
            remote_path=f"/videos/{file.name}"
        )
        for file in files_to_upload
    ]
    await asyncio.gather(*upload_tasks)
    
    # Параллельное скачивание
    download_tasks = [
        source.download_file(
            remote_path=f"/videos/{file.name}",
            local_path=Path("downloads") / file.name
        )
        for file in files_to_upload
    ]
    await asyncio.gather(*download_tasks)
    
    await source.disconnect()

asyncio.run(main())
```

### Пример 5: Замер производительности

См. файлы `run_sync.py` и `run_async.py` (точки входа) или `tests/examples/example_sync.py` и `tests/examples/example_async.py` (функции примеров) для полных примеров с замерами времени выполнения операций, включая тесты с множественными файлами (15 видео файлов по 1 MB).

**Запуск:**
```bash
# Синхронная версия
poetry run python run_sync.py

# Асинхронная версия
poetry run python run_async.py
```

### Пример 5: Обработка исключений

```python
from src.neuro_cloud_api import (
    YadiskSource,
    ConnectionError,
    AuthenticationError,
    UploadError,
    DownloadError,
)

try:
    source = YadiskSource(token="your_token")
    source.connect()
    source.upload_file("file.txt", "/file.txt")
except AuthenticationError:
    print("Неверный токен")
except ConnectionError as e:
    print(f"Ошибка подключения: {e}")
except UploadError as e:
    print(f"Ошибка загрузки: {e}")
```

---

## Паттерны проектирования

### 1. Abstract Factory Pattern

Базовые классы `BaseSource` и `BaseSourceAsync` определяют интерфейсы, которые реализуют конкретные классы (`YadiskSource`, `YadiskSourceAsync`).

**Преимущества:**
- Единый интерфейс для всех источников (sync и async разделены)
- Легко добавить новые типы хранилищ
- Полиморфизм
- Четкое разделение синхронных и асинхронных контрактов

**Особенность:** Синхронные и асинхронные интерфейсы разделены на отдельные базовые классы (`BaseSource` и `BaseSourceAsync`), что предотвращает смешивание sync и async методов.

### 2. Factory Pattern

Класс `SourceFactory` инкапсулирует логику создания объектов источников.

**Преимущества:**
- Скрывает детали создания объектов
- Централизованная логика выбора источника
- Легко расширять новыми типами

### 3. Strategy Pattern

Различные реализации (`YadiskSource`, `YadiskSourceAsync`) представляют разные стратегии работы с хранилищем.

**Преимущества:**
- Возможность выбора между синхронным и асинхронным подходом
- Легко переключаться между стратегиями

### 4. Публичный API через api.py

Все публичные классы, интерфейсы и исключения экспортируются через `api.py`, а `__init__.py` является тонким реэкспортом. Это обеспечивает четкий контракт библиотеки и упрощает поддержку.

---

## Производительность

### Сравнение синхронной и асинхронной версий

На основе тестов с типичными операциями:

#### Одиночные операции

| Операция | Синхронная версия | Асинхронная версия | Примечание |
|----------|------------------|-------------------|------------|
| Список директорий (30 шт) | ~0.97 сек | ~0.90 сек | Небольшое преимущество у async |
| Поиск директорий | ~1.07 сек | ~1.48 сек | Синхронная версия быстрее для простых операций |
| Загрузка 1 файла (1 MB) | ~0.40 сек | ~0.43 сек | Примерно одинаково |
| Скачивание 1 файла (1 MB) | ~0.43 сек | ~0.54 сек | Примерно одинаково |

#### Множественные операции (15 видео файлов по 1 MB каждый)

| Операция | Синхронная версия (последовательно) | Асинхронная версия (параллельно) | Ускорение |
|----------|-------------------------------------|----------------------------------|-----------|
| Загрузка 15 файлов | ~6.0-8.0 сек | ~2.5-4.0 сек | **2-3x быстрее** |
| Среднее время на файл (загрузка) | ~0.40-0.53 сек/файл | ~0.17-0.27 сек/файл | **~2x быстрее** |
| Скачивание 15 файлов | ~6.5-9.0 сек | ~2.8-4.5 сек | **2-3x быстрее** |
| Среднее время на файл (скачивание) | ~0.43-0.60 сек/файл | ~0.19-0.30 сек/файл | **~2x быстрее** |

**Примечание:** Результаты могут варьироваться в зависимости от скорости интернет-соединения, нагрузки на сервер и размера файлов.

### Выводы

1. **Для простых операций** (загрузка/скачивание одного файла, список директорий) разница между синхронной и асинхронной версиями незначительна.

2. **Асинхронная версия показывает значительное преимущество** при работе с множеством файлов:
   - Параллельная обработка позволяет загружать/скачивать несколько файлов одновременно
   - Ускорение в 2-3 раза при работе с 10-20 файлами
   - Эффективность растет с увеличением количества файлов

3. **Асинхронная версия полезна** когда:
   - Нужно обрабатывать множество операций параллельно
   - Работаете в асинхронном приложении (например, веб-сервер)
   - Хотите неблокирующие операции
   - Работаете с большим количеством файлов (видео, изображения, документы)

4. **Синхронная версия подходит** для:
   - Простых скриптов
   - Последовательной обработки
   - Когда асинхронность не нужна
   - Работы с небольшим количеством файлов

### Пример тестирования множественных файлов

Для запуска тестов с множественными файлами используйте примеры:

```bash
# Синхронная версия (последовательная загрузка/скачивание)
poetry run python run_sync.py

# Асинхронная версия (параллельная загрузка/скачивание)
poetry run python run_async.py
```

**Примечание:** Файлы `run_sync.py` и `run_async.py` в корне проекта являются точками входа, которые импортируют функции из `tests/examples/example_sync.py` и `tests/examples/example_async.py`. Это позволяет использовать примеры как напрямую (через точки входа), так и импортировать функции в других скриптах.

Примеры автоматически создают 15 тестовых видео файлов (по 1 MB каждый), загружают и скачивают их, выводя детальную статистику по времени выполнения.

---

## Расширение библиотеки

### Добавление нового типа источника

1. **Создайте класс**, наследующийся от `BaseSource` (для sync) или `BaseSourceAsync` (для async):

```python
from .base_source import BaseSource
from .source_type import SourceType

class NewSource(BaseSource):
    def __init__(self, token: str):
        super().__init__(token, source_type=SourceType.NEW_SOURCE)
        self._client = None  # Инициализация клиента
    
    def connect(self) -> bool:
        # Реализация подключения
        pass
    
    # Реализация остальных абстрактных методов
```

Для асинхронной версии используйте `BaseSourceAsync` и `async def` методы.

2. **Добавьте тип в SourceType enum**:

```python
class SourceType(Enum):
    # ...
    NEW_SOURCE = "new_source"
```

3. **Обновите SourceFactory**:

```python
def create_source(...):
    # ...
    elif source_type_enum == SourceType.NEW_SOURCE:
        return NewSource(token=token)
```

---

## Обработка ошибок

Библиотека использует иерархию пользовательских исключений, определенных в `errors.py`:

### Иерархия исключений

- `NeuroCloudAPIError` — базовое исключение для всех ошибок библиотеки
  - `ConnectionError` — ошибка подключения к облачному хранилищу
  - `AuthenticationError` — ошибка аутентификации (неверный токен)
  - `FileNotFoundError` — файл не найден в облачном хранилище
  - `UploadError` — ошибка загрузки файла
  - `DownloadError` — ошибка скачивания файла
  - `SourceNotImplementedError` — источник еще не реализован

### Использование

Все методы выбрасывают соответствующие исключения при ошибках. Рекомендуется использовать try/except для обработки:

```python
from src.neuro_cloud_api import (
    YadiskSource,
    ConnectionError,
    AuthenticationError,
    UploadError,
)

try:
    source = YadiskSource(token="token")
    source.connect()
    source.upload_file("file.txt", "/file.txt")
except AuthenticationError:
    print("Неверный токен")
except ConnectionError as e:
    print(f"Ошибка подключения: {e.message}")
except UploadError as e:
    print(f"Ошибка загрузки: {e.message}")
```

---

## Лицензия

См. файл `LICENSE` в корне проекта.

---

## Поддержка

Для вопросов и предложений создайте issue в репозитории проекта.

---

**Версия документации:** 2.0  
**Дата последнего обновления:** 2024
