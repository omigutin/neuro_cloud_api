# Neuro Cloud API

Python-библиотека с единым интерфейсом к облачным хранилищам: Яндекс.Диск (sync и async);
Google Drive и S3 — заглушки.

- канонические remote-пути (`/Folder/file.txt`, без `disk:`);
- метаданные в модели `StorageItem`;
- собственная иерархия исключений с базовым `NeuroCloudError`;
- `exists`, `get_item`, `iter_items`/`list_items`, `mkdir`, `upload_file`, `download_file`, `delete`,
  `move`, `copy`; перезапись только при `overwrite=True`.

## Установка

Требуется Python 3.10+.

```bash
poetry install                # разработка
poetry install --with dev     # + pytest, mypy, black, flake8
```

Как зависимость другого проекта:

```bash
pip install "git+https://github.com/omigutin/neuro_cloud_api.git@main"
```

Для примеров и e2e-тестов — файл `.env` в корне:

```env
YADISK_TOKEN=your_yandex_disk_token_here
```

## Использование

```python
import os

from neuro_cloud_api import NeuroCloudError, YadiskSource

try:
    with YadiskSource(token=os.environ["YADISK_TOKEN"]) as source:
        dirs = [item.path for item in source.list_items("/") if item.is_dir]
        source.upload_file("local_file.txt", "/Backup/remote_file.txt", overwrite=True)
except NeuroCloudError as e:
    print(f"Ошибка хранилища: {e}")
```

Асинхронно:

```python
import asyncio
import os

from neuro_cloud_api import YadiskSourceAsync


async def main() -> None:
    async with YadiskSourceAsync(token=os.environ["YADISK_TOKEN"]) as source:
        items = await source.list_items("/")
        await source.download_file("/Backup/remote_file.txt", "downloads/remote_file.txt", overwrite=True)


asyncio.run(main())
```

Через фабрику: `SourceFactory.create_source(token=..., source_type=SourceType.YANDEX_DISK)` /
`SourceFactory.create_async_source(...)`.

## Примеры

```bash
poetry run python run_sync.py    # последовательная загрузка/скачивание 15 файлов
poetry run python run_async.py   # то же параллельно
```

`run_sync.py` и `run_async.py` вызывают функции из `tests/examples/`.

## Разработка

```bash
poetry run pytest                # юнит-тесты; e2e без YADISK_TOKEN пропускаются
poetry run mypy src/
poetry run black src/
poetry run flake8 src/
```

## Структура

```
src/neuro_cloud_api/
├── api.py           # публичный API (реэкспортируется из пакета)
├── errors.py        # иерархия исключений
├── models.py        # StorageItem
├── paths.py         # контракт remote-путей
├── settings/        # NeuroCloudApiConfig
└── sources/         # BaseSource, BaseSourceAsync, Яндекс.Диск, заглушки, фабрика
tests/
├── unit/            # без сети
├── e2e/             # live smoke против Яндекс.Диска (нужен YADISK_TOKEN)
└── examples/        # примеры
```

## Документация

Полный справочник, иерархия исключений и миграция с 1.0 — [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md).

## Лицензия

См. [LICENSE](LICENSE).
