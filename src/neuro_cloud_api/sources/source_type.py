from enum import Enum


class SourceType(Enum):
    YANDEX_DISK = "yandex_disk"
    GOOGLE_DRIVE = "google_drive"
    S3 = "s3"

    @classmethod
    def from_string(cls, value: str) -> "SourceType":
        """
        Преобразует строку в SourceType.

        Args:
            value: Строковое значение типа источника

        Returns:
            SourceType enum

        Raises:
            ValueError: Если тип источника не поддерживается
        """
        value_lower = value.lower().replace("-", "_").replace(" ", "_")
        for source_type in cls:
            if source_type.value == value_lower:
                return source_type
        raise ValueError(f"Неподдерживаемый тип источника: {value}. Доступные типы: {[st.value for st in cls]}")

    @property
    def is_supported(self) -> bool:
        """Проверяет, поддерживается ли тип источника."""
        return self in {
            SourceType.YANDEX_DISK,
            SourceType.GOOGLE_DRIVE,
            SourceType.S3,
        }
