"""Opt-in live smoke-тест против настоящего Яндекс.Диска.

Запускается ТОЛЬКО если задан env ``YADISK_TOKEN``; иначе весь модуль
пропускается (это и есть механизм opt-in). Токен берётся исключительно из
окружения — не коммитится, не пишется в фикстуры, не логируется.

Все операции происходят строго внутри выделенного корня ``/NeuroCloudApiTests``
(в уникальном подкаталоге на каждый запуск). Перед любой разрушающей операцией
путь проверяется помощником :func:`_assert_in_test_root`, поэтому тест
физически не может тронуть данные вне тестового корня.

Запуск::

    # PowerShell
    $env:YADISK_TOKEN = "<token>"; poetry run pytest tests/e2e -v

Примечание: при активном системном SOCKS-прокси httpx/requests могут не
достучаться до API — временно очистите proxy-переменные окружения.
"""

import os
import uuid
from pathlib import Path

import pytest

pytest.importorskip("yadisk")

from neuro_cloud_api import (
    YadiskSource,
    YadiskSourceAsync,
    StorageItemKind,
    RemoteExistsError,
    RemoteNotFoundError,
    LocalExistsError,
)

_TOKEN = os.getenv("YADISK_TOKEN")

pytestmark = pytest.mark.skipif(
    not _TOKEN,
    reason="YADISK_TOKEN не задан; live smoke-тест является opt-in",
)

TEST_ROOT = "/NeuroCloudApiTests"
_PAYLOAD = b"neuro_cloud_api smoke payload"


def _new_run_root() -> str:
    """Уникальный подкаталог тестового корня на каждый запуск."""
    return f"{TEST_ROOT}/run_{uuid.uuid4().hex[:12]}"


def _assert_in_test_root(path: str) -> None:
    """Страховка: запрещаем любые операции вне выделенного тестового корня."""
    assert path == TEST_ROOT or path.startswith(TEST_ROOT + "/"), (
        f"Smoke-тест отказывается работать с путём вне {TEST_ROOT}: {path}"
    )


def test_sync_smoke(tmp_path):
    run_root = _new_run_root()
    _assert_in_test_root(run_root)

    local = tmp_path / "hello.txt"
    local.write_bytes(_PAYLOAD)

    remote = f"{run_root}/hello.txt"
    copy_dst = f"{run_root}/hello_copy.txt"
    move_dst = f"{run_root}/hello_moved.txt"
    for p in (remote, copy_dst, move_dst):
        _assert_in_test_root(p)

    source = YadiskSource(token=_TOKEN)
    with source:
        assert source.check_connection() is True

        source.mkdir(run_root)  # parents=True создаёт и TEST_ROOT
        try:
            assert source.exists(run_root) is True

            # upload
            source.upload_file(local, remote)
            assert source.exists(remote) is True

            # metadata
            item = source.get_item(remote)
            assert item.kind is StorageItemKind.FILE
            assert item.size == len(_PAYLOAD)
            assert item.path == remote

            # listing
            names = [i.name for i in source.list_items(run_root)]
            assert "hello.txt" in names

            # overwrite conflict (remote)
            with pytest.raises(RemoteExistsError):
                source.upload_file(local, remote, overwrite=False)
            source.upload_file(local, remote, overwrite=True)  # ок

            # download + local overwrite conflict
            downloaded = tmp_path / "downloaded.txt"
            source.download_file(remote, downloaded)
            assert downloaded.read_bytes() == _PAYLOAD
            with pytest.raises(LocalExistsError):
                source.download_file(remote, downloaded, overwrite=False)

            # copy (server-side)
            source.copy(remote, copy_dst)
            assert source.exists(copy_dst) is True

            # move
            source.move(copy_dst, move_dst)
            assert source.exists(move_dst) is True
            assert source.exists(copy_dst) is False

            # delete + not-found семантика
            source.delete(move_dst)
            assert source.exists(move_dst) is False
            with pytest.raises(RemoteNotFoundError):
                source.get_item(move_dst)
        finally:
            _assert_in_test_root(run_root)
            source.delete(run_root, recursive=True)

        assert source.exists(run_root) is False


async def test_async_smoke(tmp_path):
    run_root = _new_run_root()
    _assert_in_test_root(run_root)

    local = tmp_path / "hello.txt"
    local.write_bytes(_PAYLOAD)

    remote = f"{run_root}/hello.txt"
    copy_dst = f"{run_root}/hello_copy.txt"
    move_dst = f"{run_root}/hello_moved.txt"
    for p in (remote, copy_dst, move_dst):
        _assert_in_test_root(p)

    source = YadiskSourceAsync(token=_TOKEN)
    async with source:
        assert await source.check_connection() is True

        await source.mkdir(run_root)
        try:
            assert await source.exists(run_root) is True

            await source.upload_file(local, remote)
            assert await source.exists(remote) is True

            item = await source.get_item(remote)
            assert item.kind is StorageItemKind.FILE
            assert item.size == len(_PAYLOAD)
            assert item.path == remote

            names = [i.name for i in await source.list_items(run_root)]
            assert "hello.txt" in names

            with pytest.raises(RemoteExistsError):
                await source.upload_file(local, remote, overwrite=False)
            await source.upload_file(local, remote, overwrite=True)

            downloaded = tmp_path / "downloaded.txt"
            await source.download_file(remote, downloaded)
            assert downloaded.read_bytes() == _PAYLOAD
            with pytest.raises(LocalExistsError):
                await source.download_file(remote, downloaded, overwrite=False)

            await source.copy(remote, copy_dst)
            assert await source.exists(copy_dst) is True

            await source.move(copy_dst, move_dst)
            assert await source.exists(move_dst) is True
            assert await source.exists(copy_dst) is False

            await source.delete(move_dst)
            assert await source.exists(move_dst) is False
            with pytest.raises(RemoteNotFoundError):
                await source.get_item(move_dst)
        finally:
            _assert_in_test_root(run_root)
            await source.delete(run_root, recursive=True)

        assert await source.exists(run_root) is False
