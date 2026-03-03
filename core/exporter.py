from pathlib import Path
from typing import List

import pandas as pd

from models.schema import CatalogRow


class ExcelExporter:
    """
    Экспорт строк каталога в Excel.
    """

    def export(
            self,
            rows: List[CatalogRow],
            output_file: Path,
    ) -> None:
        """
        :param rows: список валидированных строк
        :param output_file: путь сохранения
        """

        if not rows:
            raise ValueError("Нет данных для экспорта")

        # поля модели из схемы
        columns = list(CatalogRow.model_fields.keys())

        data = [
            row.model_dump()
            for row in rows
        ]

        df = pd.DataFrame(data, columns=columns)

        df.to_excel(output_file, index=False)
