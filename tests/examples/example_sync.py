import os
import time
import sys
from pathlib import Path
from typing import List
from dotenv import load_dotenv

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


def run_sync_example():
    total_start_time = time.perf_counter()
    
    # Переменные для статистики множественных операций
    upload_many_time = 0
    download_many_time = 0
    avg_upload_time = 0
    avg_download_time = 0
    
    try:
        # Используем Factory для создания источника
        source = SourceFactory.create_source(
            token=yadisk_token,
            source_type=SourceType.YANDEX_DISK
        )

        print("Connecting...")
        connect_start = time.perf_counter()
        try:
            source.connect()
            connect_time = time.perf_counter() - connect_start
            print(f"Connected (время подключения: {connect_time:.3f} сек)")
        except (ConnectionError, AuthenticationError) as e:
            print(f"Connection failed: {e}")
            return

        print("\nListing directories in root:")
        list_start = time.perf_counter()
        try:
            dirs = source.list_directories("/")
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
            found = source.search_directories("test", "/")
            search_time = time.perf_counter() - search_start
            for d in found:
                print(" -", d)
            print(f"Найдено директорий с 'test': {len(found)} (время: {search_time:.3f} сек)")
        except ConnectionError as e:
            print(f"Ошибка поиска директорий: {e}")
            search_time = time.perf_counter() - search_start

        print("\nUploading file...")
        upload_start = time.perf_counter()
        try:
            source.upload_file(
                local_path="test_upload.txt",
                remote_path="/test_upload.txt"
            )
            upload_time = time.perf_counter() - upload_start
            print(f"Время загрузки: {upload_time:.3f} сек")
        except (FileNotFoundError, UploadError) as e:
            print(f"Ошибка загрузки: {e}")
            upload_time = time.perf_counter() - upload_start

        print("\nDownloading file...")
        download_start = time.perf_counter()
        try:
            source.download_file(
                remote_path="/test_upload.txt",
                local_path=Path("downloads/test_upload.txt")
            )
            download_time = time.perf_counter() - download_start
            print(f"Время скачивания: {download_time:.3f} сек")
        except DownloadError as e:
            print(f"Ошибка скачивания: {e}")
            download_time = time.perf_counter() - download_start

        # Тест загрузки множества файлов
        print("\n" + "="*50)
        print("ТЕСТ ЗАГРУЗКИ МНОЖЕСТВА ФАЙЛОВ (15 видео файлов по 1 MB)")
        print("="*50)
        
        test_files = create_test_video_files(count=15, size_mb=1.0)
        remote_dir = "/test_videos_sync"
        
        print(f"\nЗагрузка {len(test_files)} файлов последовательно...")
        upload_many_start = time.perf_counter()
        upload_times = []
        successful_uploads = 0
        
        for i, local_file in enumerate(test_files, 1):
            remote_path = f"{remote_dir}/{local_file.name}"
            file_start = time.perf_counter()
            try:
                source.upload_file(local_path=local_file, remote_path=remote_path)
                file_time = time.perf_counter() - file_start
                upload_times.append(file_time)
                successful_uploads += 1
                print(f"  [{i}/{len(test_files)}] {local_file.name}: {file_time:.3f} сек")
            except UploadError as e:
                print(f"  [{i}/{len(test_files)}] Ошибка загрузки {local_file.name}: {e}")
                upload_times.append(time.perf_counter() - file_start)
        
        upload_many_time = time.perf_counter() - upload_many_start
        avg_upload_time = sum(upload_times) / len(upload_times) if upload_times else 0
        print(f"\nЗагружено файлов: {successful_uploads}/{len(test_files)}")
        print(f"Общее время загрузки: {upload_many_time:.3f} сек")
        print(f"Среднее время на файл: {avg_upload_time:.3f} сек")
        
        # Тест скачивания множества файлов
        print("\n" + "="*50)
        print("ТЕСТ СКАЧИВАНИЯ МНОЖЕСТВА ФАЙЛОВ (15 видео файлов)")
        print("="*50)
        
        download_dir = Path("downloads/test_videos_sync")
        download_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\nСкачивание {len(test_files)} файлов последовательно...")
        download_many_start = time.perf_counter()
        download_times = []
        successful_downloads = 0
        
        for i, local_file in enumerate(test_files, 1):
            remote_path = f"{remote_dir}/{local_file.name}"
            local_download_path = download_dir / local_file.name
            file_start = time.perf_counter()
            try:
                source.download_file(
                    remote_path=remote_path,
                    local_path=local_download_path
                )
                file_time = time.perf_counter() - file_start
                download_times.append(file_time)
                successful_downloads += 1
                print(f"  [{i}/{len(test_files)}] {local_file.name}: {file_time:.3f} сек")
            except DownloadError as e:
                print(f"  [{i}/{len(test_files)}] Ошибка скачивания {local_file.name}: {e}")
                download_times.append(time.perf_counter() - file_start)
        
        download_many_time = time.perf_counter() - download_many_start
        avg_download_time = sum(download_times) / len(download_times) if download_times else 0
        print(f"\nСкачано файлов: {successful_downloads}/{len(test_files)}")
        print(f"Общее время скачивания: {download_many_time:.3f} сек")
        print(f"Среднее время на файл: {avg_download_time:.3f} сек")
        
        # Очистка тестовых файлов
        print("\nОчистка локальных тестовых файлов...")
        cleanup_test_files(test_files)

        source.disconnect()
        print("\nDisconnected")
        
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return
    
    total_time = time.perf_counter() - total_start_time
    
    print("\n" + "="*50)
    print("ИТОГОВАЯ СТАТИСТИКА (СИНХРОННАЯ ВЕРСИЯ):")
    print("="*50)
    print(f"Подключение:              {connect_time:.3f} сек")
    print(f"Список директорий:        {list_time:.3f} сек")
    print(f"Поиск директорий:         {search_time:.3f} сек")
    print(f"Загрузка 1 файла:         {upload_time:.3f} сек")
    print(f"Скачивание 1 файла:      {download_time:.3f} сек")
    if upload_many_time > 0:
        print(f"Загрузка 15 файлов:       {upload_many_time:.3f} сек (среднее: {avg_upload_time:.3f} сек/файл)")
    if download_many_time > 0:
        print(f"Скачивание 15 файлов:      {download_many_time:.3f} сек (среднее: {avg_download_time:.3f} сек/файл)")
    print(f"{'='*50}")
    print(f"ОБЩЕЕ ВРЕМЯ:              {total_time:.3f} сек")
    print("="*50)


if __name__ == "__main__":
    run_sync_example()
