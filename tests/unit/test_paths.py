"""Юнит-тесты canonical remote-path contract (без сети/yadisk)."""

import pytest

from neuro_cloud_api.paths import normalize_remote_path, remote_parent, remote_name


class TestNormalize:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("/", "/"),
            ("/a", "/a"),
            ("/a/b/c", "/a/b/c"),
            ("/a//b", "/a/b"),
            ("/a/b/", "/a/b"),
            ("/a/./b", "/a/b"),
            ("/a/../b", "/b"),
            ("//a//b//", "/a/b"),
            ("  /a/b  ", "/a/b"),
        ],
    )
    def test_canonicalization(self, raw, expected):
        assert normalize_remote_path(raw) == expected

    def test_backslash_rejected(self):
        with pytest.raises(ValueError):
            normalize_remote_path("/a\\b")

    def test_relative_rejected(self):
        with pytest.raises(ValueError):
            normalize_remote_path("a/b")

    def test_provider_prefix_rejected(self):
        with pytest.raises(ValueError):
            normalize_remote_path("disk:/a/b")

    def test_non_string_rejected(self):
        with pytest.raises(ValueError):
            normalize_remote_path(None)  # type: ignore[arg-type]


class TestParent:
    @pytest.mark.parametrize(
        "path,expected",
        [
            ("/a/b/c", "/a/b"),
            ("/a", "/"),
            ("/", "/"),
            ("/a/b/", "/a"),
        ],
    )
    def test_parent(self, path, expected):
        assert remote_parent(path) == expected


class TestName:
    @pytest.mark.parametrize(
        "path,expected",
        [("/a/b/c", "c"), ("/a", "a"), ("/", "")],
    )
    def test_name(self, path, expected):
        assert remote_name(path) == expected
