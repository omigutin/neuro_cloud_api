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
BaseSource (ABC)
    ├── YadiskSource (синхронный)
    └── AsyncYadiskSource (асинхронный, наследуется от BaseSource)

SourceFactory
    ├── parse()
    ├── create_source()
    ├── create_async_source()
    └── create_source_from_config()

SourceType (Enum)
    ├── YANDEX_DISK
    ├── GOOGLE_DRIVE
    └── S3

NeuroCloudApiConfig (dataclass)
```

**Важно:** `AsyncYadiskSource` наследуется от обычного `BaseSource`, а не от отдельного асинхронного базового класса. Это позволяет использовать единый интерфейс для синхронных и асинхронных реализаций.

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
poetry run python run.py
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
│       ├── __init__.py                 # Экспорт основных классов
│       ├── sources/
│       │   ├── __init__.py
│       │   ├── base_source.py          # Базовый абстрактный класс
│       │   ├── yadisk_source.py        # Синхронная реализация для Яндекс.Диска
│       │   ├── async_yadisk_source.py  # Асинхронная реализация для Яндекс.Диска
│       │   ├── source_factory.py       # Фабрика для создания источников
│       │   ├── source_type.py          # Enum типов источников
│       │   ├── ggldisk_source.py       # Заглушка для Google Drive
│       │   └── s3_source.py            # Заглушка для S3
│       └── settings/
│           └── config.py               # Конфигурация NeuroCloudApiConfig
├── run.py                              # Пример синхронного использования
├── run_async.py                        # Пример асинхронного использования
├── pyproject.toml                      # Конфигурация Poetry
├── poetry.lock                         # Файл блокировки зависимостей (генерируется автоматически)
├── README.md                           # Краткое описание и инструкции
└── DOCUMENTATION.md                    # Полная документация
```

---

## Основные компоненты

### 1. BaseSource (Базовый абстрактный класс)

**Файл:** `src/neuro_cloud_api/sources/base_source.py`

Абстрактный базовый класс, определяющий интерфейс для всех источников облачных хранилищ. Используется как для синхронных, так и для асинхронных реализаций.

#### Атрибуты

- `token: str` — токен для авторизации
- `source_type: Enum` — тип источника (SourceType)
- `client` — клиент облачного хранилища
- `is_connected: bool` — статус подключения

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

### 3. AsyncYadiskSource (Асинхронная реализация)

**Файл:** `src/neuro_cloud_api/sources/async_yadisk_source.py`

Асинхронная реализация для работы с Яндекс.Диском. Наследуется от `BaseSource`, все методы являются асинхронными и должны вызываться с `await`.

#### Инициализация

```python
source = AsyncYadiskSource(token="your_token")
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
    source = AsyncYadiskSource(token="your_token")
    await source.connect()
    dirs = await source.list_directories("/")
    await source.disconnect()

asyncio.run(main())
```

---

### 4. SourceFactory (Фабрика источников)

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

##### `create_async_source(...) -> BaseSource`

Аналогично `create_source()`, но создает асинхронный источник.

##### `create_source_from_config(config: NeuroCloudApiConfig) -> BaseSource`

Создает источник на основе конфигурации. Автоматически выбирает синхронный или асинхронный источник в зависимости от параметра `async_enabled` в конфиге.

**Пример:**
```python
config = NeuroCloudApiConfig(
    token="your_token",
    source_type=SourceType.YANDEX_DISK,
    home_folder="/",
    async_enabled=True  # Создаст AsyncYadiskSource
)
source = SourceFactory.create_source_from_config(config)
```

---

### 5. SourceType (Enum типов источников)

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

### 6. NeuroCloudApiConfig (Конфигурация)

**Файл:** `src/neuro_cloud_api/settings/config.py`

Dataclass для хранения конфигурации библиотеки.

#### Поля

- `token: str` — токен для подключения к облачному сервису
- `source_type: Enum` — тип сервиса (SourceType)
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

```python
from src.neuro_cloud_api import (
    YadiskSource,
    AsyncYadiskSource,
    SourceFactory,
    SourceType
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
from src.neuro_cloud_api import AsyncYadiskSource

load_dotenv()
token = os.getenv('YADISK_TOKEN')

async def main():
    source = AsyncYadiskSource(token=token)
    
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

### Пример 4: Замер производительности

См. файлы `run.py` и `run_async.py` для полных примеров с замерами времени выполнения операций.

---

## Паттерны проектирования

### 1. Abstract Factory Pattern

Базовый класс `BaseSource` определяет интерфейс, который реализуют конкретные классы (`YadiskSource`, `AsyncYadiskSource`).

**Преимущества:**
- Единый интерфейс для всех источников
- Легко добавить новые типы хранилищ
- Полиморфизм

**Особенность:** `AsyncYadiskSource` наследуется от того же `BaseSource`, что и `YadiskSource`, что обеспечивает единообразие интерфейса.

### 2. Factory Pattern

Класс `SourceFactory` инкапсулирует логику создания объектов источников.

**Преимущества:**
- Скрывает детали создания объектов
- Централизованная логика выбора источника
- Легко расширять новыми типами

### 3. Strategy Pattern

Различные реализации (`YadiskSource`, `AsyncYadiskSource`) представляют разные стратегии работы с хранилищем.

**Преимущества:**
- Возможность выбора между синхронным и асинхронным подходом
- Легко переключаться между стратегиями

---

## Производительность

### Сравнение синхронной и асинхронной версий

На основе тестов с типичными операциями:

| Операция | Синхронная версия | Асинхронная версия | Примечание |
|----------|------------------|-------------------|------------|
| Список директорий (30 шт) | ~0.97 сек | ~0.90 сек | Небольшое преимущество у async |
| Поиск директорий | ~1.07 сек | ~1.48 сек | Синхронная версия быстрее для простых операций |
| Загрузка файла | ~0.40 сек | ~0.43 сек | Примерно одинаково |
| Скачивание файла | ~0.43 сек | ~0.54 сек | Примерно одинаково |

### Выводы

1. **Для простых операций** (загрузка/скачивание одного файла, список директорий) разница между синхронной и асинхронной версиями незначительна.

2. **Асинхронная версия полезна** когда:
   - Нужно обрабатывать множество операций параллельно
   - Работаете в асинхронном приложении (например, веб-сервер)
   - Хотите неблокирующие операции

3. **Синхронная версия подходит** для:
   - Простых скриптов
   - Последовательной обработки
   - Когда асинхронность не нужна

---

## Расширение библиотеки

### Добавление нового типа источника

1. **Создайте класс**, наследующийся от `BaseSource`:

```python
from .base_source import BaseSource
from .source_type import SourceType

class NewSource(BaseSource):
    def __init__(self, token: str):
        super().__init__(token, source_type=SourceType.NEW_SOURCE)
        # Инициализация клиента
    
    def connect(self) -> bool:
        # Реализация подключения
        pass
    
    # Реализация остальных абстрактных методов
```

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

Библиотека обрабатывает следующие типы ошибок:

- `yadisk.exceptions.UnauthorizedError` — неверный токен
- `FileNotFoundError` — файл не найден
- `ValueError` — неподдерживаемый тип источника
- `NotImplementedError` — источник еще не реализован

Все методы возвращают `False` при ошибках или выбрасывают исключения в зависимости от критичности.

---

## Лицензия

См. файл `LICENSE` в корне проекта.

---

## Поддержка

Для вопросов и предложений создайте issue в репозитории проекта.

---

**Версия документации:** 2.0  
**Дата последнего обновления:** 2024
