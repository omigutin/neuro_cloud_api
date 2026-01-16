# Neuro Cloud API

Python библиотека для работы с облачными хранилищами данных (Яндекс.Диск, Google Drive, S3).

## Установка

### Требования

- Python 3.9+
- Poetry (для управления зависимостями)

### Установка Poetry

Если у вас еще не установлен Poetry:

```bash
# Linux/macOS
curl -sSL https://install.python-poetry.org | python3 -

# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

Или через pip:

```bash
pip install poetry
```

### Установка проекта

1. Клонируйте репозиторий:

```bash
git clone <repository-url>
cd yadisk_api
```

2. Установите зависимости через Poetry:

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

## Настройка

Создайте файл `.env` в корне проекта:

```env
YADISK_TOKEN=your_yandex_disk_token_here
```

## Использование

### Базовый пример (синхронно)

```python
import os
from dotenv import load_dotenv
from src.neuro_cloud_api import YadiskSource

load_dotenv()
source = YadiskSource(token=os.getenv('YADISK_TOKEN'))

if source.connect():
    dirs = source.list_directories("/")
    source.upload_file("local_file.txt", "/remote_file.txt")
    source.disconnect()
```

### Асинхронный пример

```python
import os
import asyncio
from dotenv import load_dotenv
from src.neuro_cloud_api import AsyncYadiskSource

load_dotenv()

async def main():
    source = AsyncYadiskSource(token=os.getenv('YADISK_TOKEN'))
    await source.connect()
    dirs = await source.list_directories("/")
    await source.disconnect()

asyncio.run(main())
```

## Запуск примеров

```bash
# Синхронный пример
poetry run python run.py

# Асинхронный пример
poetry run python run_async.py
```

## Разработка

### Установка зависимостей для разработки

```bash
poetry install --with dev
```

### Запуск тестов

```bash
poetry run pytest
```

### Форматирование кода

```bash
poetry run black src/
```

### Проверка типов

```bash
poetry run mypy src/
```

### Линтинг

```bash
poetry run flake8 src/
```

## Структура проекта

```
yadisk_api/
├── src/
│   └── neuro_cloud_api/      # Основной пакет
│       ├── sources/           # Реализации источников
│       └── settings/          # Конфигурация
├── run.py                     # Пример синхронного использования
├── run_async.py              # Пример асинхронного использования
├── pyproject.toml            # Конфигурация Poetry
└── DOCUMENTATION.md          # Полная документация
```

## Зависимости

- `yadisk` - библиотека для работы с Яндекс.Диском
- `python-dotenv` - загрузка переменных окружения

## Документация

Полная документация доступна в файле [DOCUMENTATION.md](DOCUMENTATION.md).

## Лицензия

См. файл [LICENSE](LICENSE).
