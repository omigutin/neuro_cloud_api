"""Canonical remote-path contract (provider-independent).

Единые правила для remote paths во всех публичных операциях:

* абсолютный путь;
* root = ``"/"``;
* путь начинается с ``"/"``;
* separator = ``"/"``;
* префиксы провайдера (``disk:`` и т.п.) наружу не выходят и на входе не
  принимаются;
* Windows-separator ``"\\"`` как remote separator не принимается.

Модуль чистый (без ввода-вывода и без ``yadisk``): нормализацию/валидацию
используют все storage-операции, чтобы каждый метод не разбирал пути сам.
"""

__all__ = ["normalize_remote_path", "remote_parent", "remote_name"]


def normalize_remote_path(path: str) -> str:
    """Валидирует и приводит remote path к canonical виду.

    Схлопывает повторяющиеся ``/``, убирает ``.`` и разрешает ``..``,
    гарантирует ведущий ``/`` и отсутствие завершающего (кроме root).

    Raises:
        ValueError: если путь не строка, не абсолютный, содержит ``"\\"``
            или префикс провайдера.
    """
    if not isinstance(path, str):
        raise ValueError(f"remote path должен быть строкой, получено: {type(path)!r}")

    raw = path.strip()
    if "\\" in raw:
        raise ValueError(f"remote path не должен содержать '\\': {path!r}")
    if ":" in raw.split("/", 1)[0]:
        # напр. "disk:/foo" — префикс провайдера не является частью контракта
        raise ValueError(f"remote path не должен содержать префикс провайдера: {path!r}")
    if not raw.startswith("/"):
        raise ValueError(f"remote path должен быть абсолютным (начинаться с '/'): {path!r}")

    parts: list[str] = []
    for seg in raw.split("/"):
        if seg == "" or seg == ".":
            continue
        if seg == "..":
            if parts:
                parts.pop()
            continue
        parts.append(seg)
    return "/" + "/".join(parts)


def remote_parent(path: str) -> str:
    """Canonical путь родительского каталога. Для root возвращает ``"/"``."""
    normalized = normalize_remote_path(path)
    if normalized == "/":
        return "/"
    idx = normalized.rfind("/")
    return normalized[:idx] if idx > 0 else "/"


def remote_name(path: str) -> str:
    """Имя последнего сегмента пути. Для root возвращает ``""``."""
    normalized = normalize_remote_path(path)
    if normalized == "/":
        return ""
    return normalized[normalized.rfind("/") + 1:]
