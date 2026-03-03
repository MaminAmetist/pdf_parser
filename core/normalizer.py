from typing import List

from models.schema import CatalogRow


class CatalogNormalizer:
    """
    Нормализация строк каталога.

    Дублирует строки, если одновременно заполнено
    несколько колонок P / M / K.
    """

    _GRADE_FIELDS = ("P", "M", "K")

    def expand_alloys(self, rows: List[CatalogRow]) -> List[CatalogRow]:
        """
        Если строка содержит несколько заполненных
        колонок P / M / K, создаёт отдельную строку
        для каждой из них.
        """

        if not isinstance(rows, list):
            raise TypeError("rows должен быть списком CatalogRow")

        result: List[CatalogRow] = []

        for row in rows:
            filled = [
                field
                for field in self._GRADE_FIELDS
                if getattr(row, field) is not None
            ]

            # Если заполнена только одна
            if len(filled) <= 1:
                result.append(row)
                continue

            # Если заполнено несколько
            for field in filled:
                row_data = row.model_dump()

                # Обнуляет все кроме текущего
                for f in self._GRADE_FIELDS:
                    if f != field:
                        row_data[f] = None

                result.append(CatalogRow(**row_data))

        return result
