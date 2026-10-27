"""Юнит-тесты SourceType (без сети и без yadisk)."""

import pytest

from neuro_cloud_api.sources.source_type import SourceType


class TestFromString:
    @pytest.mark.parametrize(
        "value",
        ["yandex_disk", "YANDEX_DISK", "yandex-disk", "yandex disk", "Yandex-Disk"],
    )
    def test_yandex_variants(self, value):
        assert SourceType.from_string(value) == SourceType.YANDEX_DISK

    def test_google(self):
        assert SourceType.from_string("google_drive") == SourceType.GOOGLE_DRIVE

    def test_s3(self):
        assert SourceType.from_string("s3") == SourceType.S3

    def test_unknown_raises_value_error(self):
        with pytest.raises(ValueError):
            SourceType.from_string("dropbox")


class TestIsSupported:
    def test_yandex_supported(self):
        assert SourceType.YANDEX_DISK.is_supported is True
