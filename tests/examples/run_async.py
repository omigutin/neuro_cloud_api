import os
import time
import sys
from dotenv import load_dotenv

import asyncio
from pathlib import Path

# Добавляем путь к корню проекта для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from src.neuro_cloud_api import (
    SourceFactory,
    SourceType,
    ConnectionError,
    AuthenticationError,
    FileNotFoundError,
    UploadError,
    DownloadError,
)


# Загружаем переменные из .env файла
load_dotenv()

# Считываем токен
yadisk_token = os.getenv('YADISK_TOKEN')


async def main():
    total_start_time = time.perf_counter()
    
    try:
        # Используем Factory для создания асинхронного источника
        source = SourceFactory.create_async_source(
            token=yadisk_token,
            source_type=SourceType.YANDEX_DISK
        )

        print("Connecting (async)...")
        connect_start = time.perf_counter()
        try:
            await source.connect()
            connect_time = time.perf_counter() - connect_start
            print(f"Connected (async) (время подключения: {connect_time:.3f} сек)")
        except (ConnectionError, AuthenticationError) as e:
            print(f"Async connection failed: {e}")
            return

        print("\nListing directories in root:")
        list_start = time.perf_counter()
        try:
            dirs = await source.list_directories("/")
            list_time = time.perf_counter() - list_start
            for d in dirs:
                print(" -", d)
            print(f"Найдено директорий: {len(dirs)} (время: {list_time:.3f} сек)")
        except ConnectionError as e:
            print(f"Ошибка получения списка директорий: {e}")
            list_time = time.perf_counter() - list_start

        print("\nSearching directories with 'test':")
        search_start = time.perf_counter()
        try:
            found = await source.search_directories("test", "/")
            search_time = time.perf_counter() - search_start
            for d in found:
                print(" -", d)
            print(f"Найдено директорий с 'test': {len(found)} (время: {search_time:.3f} сек)")
        except ConnectionError as e:
            print(f"Ошибка поиска директорий: {e}")
            search_time = time.perf_counter() - search_start

        print("\nUploading file (async)...")
        upload_start = time.perf_counter()
        try:
            await source.upload_file(
                local_path="test_upload.txt",
                remote_path="/test_upload_async.txt"
            )
            upload_time = time.perf_counter() - upload_start
            print(f"Время загрузки: {upload_time:.3f} сек")
        except (FileNotFoundError, UploadError) as e:
            print(f"Ошибка загрузки: {e}")
            upload_time = time.perf_counter() - upload_start

        print("\nDownloading file (async)...")
        download_start = time.perf_counter()
        try:
            await source.download_file(
                remote_path="/test_upload_async.txt",
                local_path=Path("downloads_async/test_upload_async.txt")
            )
            download_time = time.perf_counter() - download_start
            print(f"Время скачивания: {download_time:.3f} сек")
        except DownloadError as e:
            print(f"Ошибка скачивания: {e}")
            download_time = time.perf_counter() - download_start

        await source.disconnect()
        print("\nDisconnected (async)")
        
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return
    
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
