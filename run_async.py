import os
import time
from dotenv import load_dotenv

import asyncio
from pathlib import Path

from src.neuro_cloud_api import SourceFactory, SourceType


# Загружаем переменные из .env файла
load_dotenv()

# Считываем токен
yadisk_token = os.getenv('YADISK_TOKEN')

async def main():
    total_start_time = time.perf_counter()
    
    # Используем Factory для создания асинхронного источника
    source = SourceFactory.create_async_source(
        token=yadisk_token,
        source_type=SourceType.YANDEX_DISK
    )

    print("Connecting (async)...")
    connect_start = time.perf_counter()
    if not await source.connect():
        print("Async connection failed")
        return
    connect_time = time.perf_counter() - connect_start
    print(f"Connected (async) (время подключения: {connect_time:.3f} сек)")

    print("\nListing directories in root:")
    list_start = time.perf_counter()
    dirs = await source.list_directories("/")
    list_time = time.perf_counter() - list_start
    for d in dirs:
        print(" -", d)
    print(f"Найдено директорий: {len(dirs)} (время: {list_time:.3f} сек)")

    print("\nSearching directories with 'test':")
    search_start = time.perf_counter()
    found = await source.search_directories("test", "/")
    search_time = time.perf_counter() - search_start
    for d in found:
        print(" -", d)
    print(f"Найдено директорий с 'test': {len(found)} (время: {search_time:.3f} сек)")

    print("\nUploading file (async)...")
    upload_start = time.perf_counter()
    await source.upload_file(
        local_path="test_upload.txt",
        remote_path="/test_upload_async.txt"
    )
    upload_time = time.perf_counter() - upload_start
    print(f"Время загрузки: {upload_time:.3f} сек")

    print("\nDownloading file (async)...")
    download_start = time.perf_counter()
    await source.download_file(
        remote_path="/test_upload_async.txt",
        local_path=Path("downloads_async/test_upload_async.txt")
    )
    download_time = time.perf_counter() - download_start
    print(f"Время скачивания: {download_time:.3f} сек")

    await source.disconnect()
    print("\nDisconnected (async)")
    
    total_time = time.perf_counter() - total_start_time
    print("\n" + "="*50)
    print("ИТОГОВАЯ СТАТИСТИКА (АСИНХРОННАЯ ВЕРСИЯ):")
    print("="*50)
    print(f"Подключение:        {connect_time:.3f} сек")
    print(f"Список директорий:  {list_time:.3f} сек")
    print(f"Поиск директорий:   {search_time:.3f} сек")
    print(f"Загрузка файла:     {upload_time:.3f} сек")
    print(f"Скачивание файла:   {download_time:.3f} сек")
    print(f"{'='*50}")
    print(f"ОБЩЕЕ ВРЕМЯ:        {total_time:.3f} сек")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main())