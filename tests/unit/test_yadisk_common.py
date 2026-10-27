"""Юнит-тесты Yandex-склейки: маппинг ресурса и трансляция исключений."""

from datetime import datetime
from types import SimpleNamespace

import pytest

yadisk = pytest.importorskip("yadisk")

from neuro_cloud_api.sources import _yadisk_common as c
from neuro_cloud_api.models import StorageItemKind
from neuro_cloud_api.errors import (
    CloudAuthenticationError,
    CloudConnectionError,
    CloudRateLimitError,
    RemoteNotFoundError,
    RemoteConflictError,
    RemoteExistsError,
    RemotePermissionError,
    LocalNotFoundError,
    LocalExistsError,
    LocalPermissionError,
    LocalFileError,
    ProviderError,
)

_exc = yadisk.exceptions


class TestStripDiskPrefix:
    def test_strips(self):
        assert c.strip_disk_prefix("disk:/Foo/bar") == "/Foo/bar"

    def test_bare_disk(self):
        assert c.strip_disk_prefix("disk:") == "/"

    def test_canonical_unchanged(self):
        assert c.strip_disk_prefix("/Foo") == "/Foo"


class TestToStorageItem:
    def test_file_mapping_with_checksum(self):
        r = SimpleNamespace(
            name="video.avi",
            type="file",
            path="disk:/Reg/video.avi",
            size=1024,
            modified=datetime(2024, 1, 2),
            created=datetime(2024, 1, 1),
            md5="abc123",
            mime_type="video/x-msvideo",
        )
        item = c.to_storage_item(r)
        assert item.name == "video.avi"
        assert item.path == "/Reg/video.avi"  # canonical, без disk:
        assert item.kind is StorageItemKind.FILE
        assert item.size == 1024
        assert item.modified_at == datetime(2024, 1, 2)
        assert item.created_at == datetime(2024, 1, 1)
        assert item.checksum == "abc123"
        assert item.checksum_algorithm == "md5"
        assert item.mime_type == "video/x-msvideo"

    def test_directory_has_no_checksum(self):
        r = SimpleNamespace(name="Reg", type="dir", path="disk:/Reg", md5="ignored")
        item = c.to_storage_item(r)
        assert item.kind is StorageItemKind.DIRECTORY
        assert item.checksum is None
        assert item.checksum_algorithm is None

    def test_file_without_md5_has_no_checksum(self):
        r = SimpleNamespace(name="a", type="file", path="disk:/a", md5=None)
        item = c.to_storage_item(r)
        assert item.checksum is None
        assert item.checksum_algorithm is None


class TestTranslateError:
    @pytest.mark.parametrize(
        "raised,expected",
        [
            (_exc.UnauthorizedError("x"), CloudAuthenticationError),
            (_exc.ForbiddenError("x"), RemotePermissionError),
            (_exc.PathNotFoundError("x"), RemoteNotFoundError),
            (_exc.NotFoundError("x"), RemoteNotFoundError),
            (_exc.PathExistsError("x"), RemoteExistsError),
            (_exc.DirectoryExistsError("x"), RemoteExistsError),
            (_exc.ParentNotFoundError("x"), RemoteConflictError),
            (_exc.TooManyRequestsError("x"), CloudRateLimitError),
            (_exc.BadRequestError("x"), ProviderError),
        ],
    )
    def test_yadisk_mapping(self, raised, expected):
        assert isinstance(c.translate_error(raised), expected)

    def test_request_error_is_connection(self):
        # RequestError — transport-уровень
        err = _exc.RequestError("boom")
        assert isinstance(c.translate_error(err), CloudConnectionError)

    def test_local_os_errors(self):
        assert isinstance(c.translate_error(FileNotFoundError("x")), LocalNotFoundError)
        assert isinstance(c.translate_error(FileExistsError("x")), LocalExistsError)
        assert isinstance(c.translate_error(PermissionError("x")), LocalPermissionError)
        assert isinstance(c.translate_error(OSError("x")), LocalFileError)

    def test_domain_error_passthrough(self):
        original = RemoteNotFoundError("keep")
        assert c.translate_error(original) is original

    def test_unknown_becomes_provider_error(self):
        assert isinstance(c.translate_error(RuntimeError("weird")), ProviderError)
