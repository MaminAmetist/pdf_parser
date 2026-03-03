from typing import List, Any

from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from models.schema import CatalogRow


class _RawCatalogRow(BaseModel):
    """
    Толерантная AI-схема.
    """

    model: str = Field(min_length=1)

    L: float | None = None
    I_C: float | None = None
    S: float | None = None
    d: float | None = None
    r: float | None = None

    P: str | None = None
    M: str | None = None
    K: str | None = None

    @field_validator("L", "I_C", "S", "d", "r", mode="before")
    @classmethod
    def parse_float(cls, value: Any) -> float | None:
        """
        Numeric normalization
        """

        if value is None:
            return None

        if isinstance(value, str):
            cleaned = value.strip().replace(",", ".")
            if not cleaned:
                return None
            return float(cleaned)

        if isinstance(value, (int, float)):
            return float(value)

        raise ValueError(f"Invalid numeric value: {value}")

    @field_validator("P", "M", "K", mode="before")
    @classmethod
    def normalize_grade(cls, value: Any) -> str | None:
        """
        Alloy normalization
        """

        if value is None:
            return None

        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None

        return value

    @model_validator(mode="after")
    def validate_grade_group(self) -> "_RawCatalogRow":
        """
        Group validation
        Минимум одно из P/M/K должно быть заполнено.
        """

        if not any([self.P, self.M, self.K]):
            raise ValueError(
                "Хотя бы одно из полей P, M, K должно быть заполнено"
            )
        return self


class CatalogParser:
    """
    Валидатор AI-ответа.
    """

    def validate(self, raw_rows: List[dict]) -> List[CatalogRow]:

        if not isinstance(raw_rows, list):
            raise TypeError("Ожидался список объектов")

        validated_rows: List[CatalogRow] = []

        for index, row in enumerate(raw_rows, start=1):
            try:
                validated = _RawCatalogRow.model_validate(row)
            except ValidationError:
                continue  # пропускает шум AI

            if None in (
                    validated.L,
                    validated.I_C,
                    validated.S,
                    validated.d,
                    validated.r,
            ):
                continue

            validated_rows.append(
                CatalogRow(
                    model=validated.model,
                    L=validated.L,
                    I_C=validated.I_C,
                    S=validated.S,
                    d=validated.d,
                    r=validated.r,
                    P=validated.P,
                    M=validated.M,
                    K=validated.K,
                )
            )

        if not validated_rows:
            raise ValueError("После валидации не осталось корректных строк")

        return validated_rows
