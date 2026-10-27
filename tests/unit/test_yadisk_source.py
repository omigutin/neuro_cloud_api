"""Юнит-тесты Yandex-источников (sync + async) с моками yadisk, без сети.

Требуют установленного ``yadisk`` (реальная зависимость), но не ходят в сеть:
клиент подменяется моками. Autouse-фикстура не даёт конструктору создавать
настоящий yadisk-клиент (иначе httpx читал бы системный proxy).
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, AsyncMock

import pytest

yadisk = pytest.importorskip("yadisk")

from neuro_cloud_api.sources.source_factory import SourceFactory
from neuro_cloud_api.sources.source_type import SourceType
from neuro_cloud_api.sources.yadisk_source import YadiskSource
from neuro_cloud_api.sources.yadisk_source_async import YadiskSourceAsync
from neuro_cloud_api.models import StorageItemKind
from neuro_cloud_api.errors import (
    CloudAuthenticationError,
    RemoteNotFoundError,
    RemoteConflictError,
    RemoteExistsError,
    LocalNotFoundError,
    LocalExistsError,
    SourceNotImplementedError,
)

_exc = yadisk.exceptions


@pytest.fixture(autouse=True)
def _no_real_yadisk_clients(monkeypatch):
    monkeypatch.setattr(yadisk, "Client", lambda *a, **k: MagicMock())
    monkeypatch.setattr(yadisk, "AsyncClient", lambda *a, **k: MagicMock())


def _res(type_, name, path, **extra):
    return SimpleNamespace(type=type_, name=name, path=path, **extra)


def _make_async_iter(items):
    async def listdir(path):
        for it in items:
            yield it
    return listdir


DIR_ITEMS = [
    _res("dir", "Photos", "disk:/Photos"),
    _res("dir", "MyTests", "disk:/MyTests"),
    _res("file", "readme.txt", "disk:/readme.txt", size=10, md5="m"),
]


def sync_source(client):
    s = YadiskSource(token="t")
    s._client = client
    return s


def async_source(client):
    s = YadiskSourceAsync(token="t")
    s._client = client
    return s


# ── exists / get_item ───────────────────────────────────────────────────────

class TestExistsGetItem:
    def test_sync_exists_normalizes_path(self):
        client = MagicMock()
        client.exists.return_value = True
        assert sync_source(client).exists("/a//b/") is True
        client.exists.assert_called_once_with("/a/b")

    async def test_async_exists(self):
        client = MagicMock()
        client.exists = AsyncMock(return_value=False)
        assert await async_source(client).exists("/x") is False

    def test_sync_get_item_maps_to_storage_item(self):
        client = MagicMock()
        client.get_meta.return_value = _res("file", "v.avi", "disk:/R/v.avi", size=5, md5="h")
        item = sync_source(client).get_item("/R/v.avi")
        assert item.path == "/R/v.avi"
        assert item.kind is StorageItemKind.FILE
        assert item.checksum == "h"

    def test_sync_get_item_missing_raises_remote_not_found(self):
        client = MagicMock()
        client.get_meta.side_effect = _exc.PathNotFoundError("nope")
        with pytest.raises(RemoteNotFoundError):
            sync_source(client).get_item("/missing")

    async def test_async_get_item_missing_raises(self):
        client = MagicMock()
        client.get_meta = AsyncMock(side_effect=_exc.PathNotFoundError("nope"))
        with pytest.raises(RemoteNotFoundError):
            await async_source(client).get_item("/missing")


# ── iter_items / list_items ─────────────────────────────────────────────────

class TestListing:
    def test_sync_list_items_returns_all_kinds(self):
        client = MagicMock()
        client.listdir.return_value = list(DIR_ITEMS)
        items = sync_source(client).list_items("/")
        assert [i.path for i in items] == ["/Photos", "/MyTests", "/readme.txt"]
        assert [i.kind for i in items] == [
            StorageItemKind.DIRECTORY,
            StorageItemKind.DIRECTORY,
            StorageItemKind.FILE,
        ]

    async def test_async_list_items(self):
        client = MagicMock()
        client.listdir = _make_async_iter(DIR_ITEMS)
        items = await async_source(client).list_items("/")
        assert [i.path for i in items] == ["/Photos", "/MyTests", "/readme.txt"]

    def test_sync_deprecated_list_directories_warns(self):
        client = MagicMock()
        client.listdir.return_value = list(DIR_ITEMS)
        with pytest.warns(DeprecationWarning):
            dirs = sync_source(client).list_directories("/")
        assert dirs == ["/Photos", "/MyTests"]

    def test_sync_deprecated_search_directories_warns(self):
        client = MagicMock()
        client.listdir.return_value = list(DIR_ITEMS)
        with pytest.warns(DeprecationWarning):
            found = sync_source(client).search_directories("test", "/")
        assert found == ["/MyTests"]


# ── mkdir ───────────────────────────────────────────────────────────────────

class TestMkdir:
    def test_sync_creates_parents_in_order(self):
        client = MagicMock()
        client.exists.return_value = False
        sync_source(client).mkdir("/a/b/c")
        assert [call.args[0] for call in client.mkdir.call_args_list] == ["/a", "/a/b", "/a/b/c"]

    async def test_async_creates_parents_in_order(self):
        client = MagicMock()
        client.exists = AsyncMock(return_value=False)
        client.mkdir = AsyncMock()
        await async_source(client).mkdir("/a/b/c")
        assert [call.args[0] for call in client.mkdir.call_args_list] == ["/a", "/a/b", "/a/b/c"]

    def test_sync_exist_ok_true_swallows(self):
        client = MagicMock()
        client.mkdir.side_effect = _exc.PathExistsError("exists")
        sync_source(client).mkdir("/x", parents=False, exist_ok=True)  # без исключения

    def test_sync_exist_ok_false_raises(self):
        client = MagicMock()
        client.mkdir.side_effect = _exc.PathExistsError("exists")
        with pytest.raises(RemoteExistsError):
            sync_source(client).mkdir("/x", parents=False, exist_ok=False)


# ── upload / download overwrite ─────────────────────────────────────────────

class TestUpload:
    def test_sync_missing_local_raises(self, tmp_path):
        with pytest.raises(LocalNotFoundError):
            sync_source(MagicMock()).upload_file(tmp_path / "nope.txt", "/r.txt")

    def test_sync_overwrite_passed_through(self, tmp_path):
        local = tmp_path / "f.txt"
        local.write_bytes(b"x")
        client = MagicMock()
        sync_source(client).upload_file(local, "/d/f.txt", overwrite=True, create_parents=False)
        client.upload.assert_called_once_with(str(local), "/d/f.txt", overwrite=True)

    def test_sync_existing_remote_raises_remote_exists(self, tmp_path):
        local = tmp_path / "f.txt"
        local.write_bytes(b"x")
        client = MagicMock()
        client.upload.side_effect = _exc.PathExistsError("exists")
        with pytest.raises(RemoteExistsError):
            sync_source(client).upload_file(local, "/d/f.txt", create_parents=False)


class TestDownload:
    def test_sync_local_exists_no_overwrite_raises(self, tmp_path):
        local = tmp_path / "f.txt"
        local.write_bytes(b"x")
        client = MagicMock()
        with pytest.raises(LocalExistsError):
            sync_source(client).download_file("/r.txt", local, overwrite=False)
        client.download.assert_not_called()

    def test_sync_download_ok(self, tmp_path):
        local = tmp_path / "sub" / "f.txt"
        client = MagicMock()
        sync_source(client).download_file("/r.txt", local, overwrite=True)
        client.download.assert_called_once_with("/r.txt", str(local))
        assert local.parent.exists()  # create_parents


# ── delete / move / copy ────────────────────────────────────────────────────

class TestDeleteMoveCopy:
    def test_sync_delete_nonempty_dir_no_recursive_raises(self):
        client = MagicMock()
        client.is_dir.return_value = True
        client.listdir.return_value = [_res("file", "a", "disk:/d/a")]
        with pytest.raises(RemoteConflictError):
            sync_source(client).delete("/d", recursive=False)
        client.remove.assert_not_called()

    def test_sync_delete_recursive_removes(self):
        client = MagicMock()
        client.is_dir.return_value = True
        sync_source(client).delete("/d", recursive=True)
        client.remove.assert_called_once_with("/d")

    def test_sync_delete_file_removes(self):
        client = MagicMock()
        client.is_dir.return_value = False
        sync_source(client).delete("/d/a.txt")
        client.remove.assert_called_once_with("/d/a.txt")

    def test_sync_move_full_paths(self):
        client = MagicMock()
        sync_source(client).move("/src/v.avi", "/arch/v.avi", overwrite=True)
        client.move.assert_called_once_with("/src/v.avi", "/arch/v.avi", overwrite=True)

    def test_sync_copy_full_paths(self):
        client = MagicMock()
        sync_source(client).copy("/src/v.avi", "/arch/v.avi")
        client.copy.assert_called_once_with("/src/v.avi", "/arch/v.avi", overwrite=False)


# ── connect / check_connection / disconnect / context manager ───────────────

class TestLifecycle:
    def test_sync_connect_ok(self):
        client = MagicMock()
        client.check_token.return_value = True
        s = sync_source(client)
        s.connect()
        assert s.is_connected is True

    def test_sync_connect_invalid_token_raises_auth(self):
        client = MagicMock()
        client.check_token.side_effect = _exc.UnauthorizedError("bad")
        with pytest.raises(CloudAuthenticationError):
            sync_source(client).connect()

    def test_sync_connect_false_token_raises_auth(self):
        client = MagicMock()
        client.check_token.return_value = False
        with pytest.raises(CloudAuthenticationError):
            sync_source(client).connect()

    def test_sync_check_connection_never_raises(self):
        client = MagicMock()
        client.check_token.side_effect = _exc.RequestError("net down")
        assert sync_source(client).check_connection() is False

    def test_sync_disconnect_closes(self):
        client = MagicMock()
        s = sync_source(client)
        s._is_connected = True
        s.disconnect()
        client.close.assert_called_once()
        assert s.is_connected is False

    def test_sync_context_manager(self):
        client = MagicMock()
        client.check_token.return_value = True
        with sync_source(client) as s:
            assert s.is_connected is True
        client.close.assert_called_once()

    async def test_async_context_manager(self):
        client = MagicMock()
        client.check_token = AsyncMock(return_value=True)
        client.close = AsyncMock()
        async with async_source(client) as s:
            assert s.is_connected is True
        client.close.assert_awaited_once()


# ── Паритет sync/async на ключевых сценариях ────────────────────────────────

class TestSyncAsyncParity:
    async def test_auth_error_same_type(self):
        sc = MagicMock()
        sc.check_token.side_effect = _exc.UnauthorizedError("bad")
        sync_exc = _capture(lambda: sync_source(sc).connect())

        ac = MagicMock()
        ac.check_token = AsyncMock(side_effect=_exc.UnauthorizedError("bad"))
        async_exc = await _capture_async(lambda: async_source(ac).connect())

        assert type(sync_exc) is type(async_exc) is CloudAuthenticationError

    async def test_missing_local_upload_same_type(self, tmp_path):
        missing = tmp_path / "nope.txt"
        sync_exc = _capture(lambda: sync_source(MagicMock()).upload_file(missing, "/r.txt"))
        async_exc = await _capture_async(
            lambda: async_source(MagicMock()).upload_file(missing, "/r.txt")
        )
        assert type(sync_exc) is type(async_exc) is LocalNotFoundError

    async def test_download_local_exists_same_type(self, tmp_path):
        local = tmp_path / "f.txt"
        local.write_bytes(b"x")
        sync_exc = _capture(
            lambda: sync_source(MagicMock()).download_file("/r.txt", local, overwrite=False)
        )
        async_exc = await _capture_async(
            lambda: async_source(MagicMock()).download_file("/r.txt", local, overwrite=False)
        )
        assert type(sync_exc) is type(async_exc) is LocalExistsError

    async def test_delete_nonempty_same_type(self):
        sc = MagicMock()
        sc.is_dir.return_value = True
        sc.listdir.return_value = [_res("file", "a", "disk:/d/a")]
        sync_exc = _capture(lambda: sync_source(sc).delete("/d", recursive=False))

        ac = MagicMock()
        ac.is_dir = AsyncMock(return_value=True)
        ac.listdir = _make_async_iter([_res("file", "a", "disk:/d/a")])
        async_exc = await _capture_async(lambda: async_source(ac).delete("/d", recursive=False))

        assert type(sync_exc) is type(async_exc) is RemoteConflictError


# ── Фабрика: паритет заглушек ────────────────────────────────────────────────

class TestFactoryParity:
    @pytest.mark.parametrize("stype", [SourceType.GOOGLE_DRIVE, SourceType.S3])
    def test_sync_not_implemented(self, stype):
        with pytest.raises(SourceNotImplementedError):
            SourceFactory.create_source(token="t", source_type=stype)

    @pytest.mark.parametrize("stype", [SourceType.GOOGLE_DRIVE, SourceType.S3])
    def test_async_not_implemented(self, stype):
        with pytest.raises(SourceNotImplementedError):
            SourceFactory.create_async_source(token="t", source_type=stype)


# ── helpers для parity ──────────────────────────────────────────────────────

def _capture(call):
    try:
        call()
    except Exception as e:
        return e
    raise AssertionError("ожидалось исключение")


async def _capture_async(call):
    try:
        await call()
    except Exception as e:
        return e
    raise AssertionError("ожидалось исключение")
