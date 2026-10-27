"""Юнит-тесты доменной модели StorageItem."""

from neuro_cloud_api.models import StorageItem, StorageItemKind


class TestStorageItem:
    def test_file_flags(self):
        item = StorageItem(name="a.txt", path="/a.txt", kind=StorageItemKind.FILE)
        assert item.is_file is True
        assert item.is_dir is False

    def test_directory_flags(self):
        item = StorageItem(name="d", path="/d", kind=StorageItemKind.DIRECTORY)
        assert item.is_dir is True
        assert item.is_file is False

    def test_is_frozen(self):
        item = StorageItem(name="a", path="/a", kind=StorageItemKind.FILE)
        try:
            item.size = 1  # type: ignore[misc]
        except Exception as e:
            assert isinstance(e, (AttributeError,))
        else:
            raise AssertionError("StorageItem должен быть frozen")
