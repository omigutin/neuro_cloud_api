import os
import time
import sys
from dotenv import load_dotenv

import asyncio
from pathlib import Path
from typing import List

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


def create_test_video_files(count: int = 15, size_mb: float = 1.0) -> List[Path]:
    """
    Создает тестовые видео файлы для загрузки.
    
    Args:
        count: Количество файлов
        size_mb: Размер каждого файла в мегабайтах
    
    Returns:
        Список путей к созданным файлам
    """
    test_files_dir = Path("test_videos")
    test_files_dir.mkdir(exist_ok=True)
    
    files = []
    size_bytes = int(size_mb * 1024 * 1024)
    
    for i in range(1, count + 1):
        file_path = test_files_dir / f"test_video_{i:02d}.mp4"
        # Создаем файл с случайными данными (имитация видео)
        with open(file_path, 'wb') as f:
            f.write(os.urandom(size_bytes))
        files.append(file_path)
        print(f"Создан тестовый файл: {file_path.name} ({size_mb:.1f} MB)")
    
    return files


def cleanup_test_files(files: List[Path]):
    """Удаляет тестовые файлы."""
    for file_path in files:
        if file_path.exists():
            file_path.unlink()
    # Удаляем директорию, если пуста
    test_files_dir = Path("test_videos")
    if test_files_dir.exists() and not any(test_files_dir.iterdir()):
        test_files_dir.rmdir()


async def run_async_example():
    total_start_time = time.perf_counter()
    
    # Переменные для статистики множественных операций
    upload_many_time = 0
    download_many_time = 0
    avg_upload_time = 0
    avg_download_time = 0
    
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

        # Тест параллельной загрузки множества файлов
        print("\n" + "="*50)
        print("ТЕСТ ПАРАЛЛЕЛЬНОЙ ЗАГРУЗКИ МНОЖЕСТВА ФАЙЛОВ (15 видео файлов по 1 MB)")
        print("="*50)
        
        test_files = create_test_video_files(count=15, size_mb=1.0)
        remote_dir = "/test_videos_async"
        
        print(f"\nПараллельная загрузка {len(test_files)} файлов...")
        upload_many_start = time.perf_counter()
        
        async def upload_file_task(local_file: Path, index: int, total: int):
            remote_path = f"{remote_dir}/{local_file.name}"
            file_start = time.perf_counter()
            try:
                await source.upload_file(local_path=local_file, remote_path=remote_path)
                file_time = time.perf_counter() - file_start
                print(f"  [{index}/{total}] {local_file.name}: {file_time:.3f} сек")
                return file_time, True
            except UploadError as e:
                print(f"  [{index}/{total}] Ошибка загрузки {local_file.name}: {e}")
                return time.perf_counter() - file_start, False
        
        # Создаем задачи для параллельной загрузки
        upload_tasks = [
            upload_file_task(file, i+1, len(test_files))
            for i, file in enumerate(test_files)
        ]
        
        upload_results = await asyncio.gather(*upload_tasks)
        upload_many_time = time.perf_counter() - upload_many_start
        
        upload_times = [result[0] for result in upload_results]
        successful_uploads = sum(1 for result in upload_results if result[1])
        avg_upload_time = sum(upload_times) / len(upload_times) if upload_times else 0
        
        print(f"\nЗагружено файлов: {successful_uploads}/{len(test_files)}")
        print(f"Общее время загрузки (параллельно): {upload_many_time:.3f} сек")
        print(f"Среднее время на файл: {avg_upload_time:.3f} сек")
        
        # Тест параллельного скачивания множества файлов
        print("\n" + "="*50)
        print("ТЕСТ ПАРАЛЛЕЛЬНОГО СКАЧИВАНИЯ МНОЖЕСТВА ФАЙЛОВ (15 видео файлов)")
        print("="*50)
        
        download_dir = Path("downloads_async/test_videos_async")
        download_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\nПараллельное скачивание {len(test_files)} файлов...")
        download_many_start = time.perf_counter()
        
        async def download_file_task(local_file: Path, index: int, total: int):
            remote_path = f"{remote_dir}/{local_file.name}"
            local_download_path = download_dir / local_file.name
            file_start = time.perf_counter()
            try:
                await source.download_file(
                    remote_path=remote_path,
                    local_path=local_download_path
                )
                file_time = time.perf_counter() - file_start
                print(f"  [{index}/{total}] {local_file.name}: {file_time:.3f} сек")
                return file_time, True
            except DownloadError as e:
                print(f"  [{index}/{total}] Ошибка скачивания {local_file.name}: {e}")
                return time.perf_counter() - file_start, False
        
        # Создаем задачи для параллельного скачивания
        download_tasks = [
            download_file_task(file, i+1, len(test_files))
            for i, file in enumerate(test_files)
        ]
        
        download_results = await asyncio.gather(*download_tasks)
        download_many_time = time.perf_counter() - download_many_start
        
        download_times = [result[0] for result in download_results]
        successful_downloads = sum(1 for result in download_results if result[1])
        avg_download_time = sum(download_times) / len(download_times) if download_times else 0
        
        print(f"\nСкачано файлов: {successful_downloads}/{len(test_files)}")
        print(f"Общее время скачивания (параллельно): {download_many_time:.3f} сек")
        print(f"Среднее время на файл: {avg_download_time:.3f} сек")
        
        # Очистка тестовых файлов
        print("\nОчистка локальных тестовых файлов...")
        cleanup_test_files(test_files)

        await source.disconnect()
        print("\nDisconnected (async)")
        
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return
    
    total_time = time.perf_counter() - total_start_time
    
    print("\n" + "="*50)
    print("ИТОГОВАЯ СТАТИСТИКА (АСИНХРОННАЯ ВЕРСИЯ):")
    print("="*50)
    print(f"Подключение:              {connect_time:.3f} сек")
    print(f"Список директорий:        {list_time:.3f} сек")
    print(f"Поиск директорий:         {search_time:.3f} сек")
    print(f"Загрузка 1 файла:         {upload_time:.3f} сек")
    print(f"Скачивание 1 файла:       {download_time:.3f} сек")
    if upload_many_time > 0:
        print(f"Параллельная загрузка 15 файлов: {upload_many_time:.3f} сек (среднее: {avg_upload_time:.3f} сек/файл)")
    if download_many_time > 0:
        print(f"Параллельное скачивание 15 файлов: {download_many_time:.3f} сек (среднее: {avg_download_time:.3f} сек/файл)")
    print(f"{'='*50}")
    print(f"ОБЩЕЕ ВРЕМЯ:              {total_time:.3f} сек")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(run_async_example())
