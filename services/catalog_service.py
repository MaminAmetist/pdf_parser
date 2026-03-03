import os
from pathlib import Path
from typing import List, Optional, Tuple

from core.exporter import ExcelExporter
from core.normalizer import CatalogNormalizer
from core.parser import CatalogParser
from core.pdf_processor import PDFProcessor
from core.vision_client import VisionClient


class CatalogService:
    """
    Оркестратор обработки каталога.
    """

    def __init__(
            self,
            input_pdf: Path,
            output_file: Path,
            prompt_path: Path,
    ) -> None:

        self.input_pdf = Path(input_pdf).resolve()
        self.output_file = Path(output_file).resolve()

        if not self.input_pdf.exists():
            raise FileNotFoundError(f"PDF не найден: {self.input_pdf}")

        api_key = os.getenv("AI_API_KEY")
        model_name = os.getenv("MODEL_NAME")

        if not api_key:
            raise ValueError("AI_API_KEY не найден в .env")

        if not model_name:
            raise ValueError("MODEL_NAME не найден в .env")

        self.pdf_processor = PDFProcessor()
        self.vision_client = VisionClient(
            api_key=api_key,
            model=model_name,
            prompt_path=Path(prompt_path).resolve(),
        )
        self.parser = CatalogParser()
        self.normalizer = CatalogNormalizer()
        self.exporter = ExcelExporter()

    def process(
            self,
            page_range: Optional[Tuple[int, int]] = None,
    ) -> None:
        """
        Полный пайплайн обработки.

        :param page_range: диапазон страниц (start, end), 1-based
        """

        if page_range is not None:
            self._validate_page_range(page_range)

        images = self.pdf_processor.convert_to_images(
            self.input_pdf,
            page_range=page_range,
        )

        if not images:
            raise ValueError("Нет страниц для обработки")

        all_raw_rows: List[dict] = []

        for page_number, image_bytes in images:
            print(f"Обработка страницы {page_number}")

            raw_rows = self.vision_client.extract_table_from_image(
                image_bytes
            )

            all_raw_rows.extend(raw_rows)

        if not all_raw_rows:
            raise ValueError("Vision не вернул ни одной строки")

        validated = self.parser.validate(all_raw_rows)
        normalized = self.normalizer.expand_alloys(validated)

        self.exporter.export(normalized, self.output_file)

        print(f"Готово. Сохранено: {self.output_file}")

    @staticmethod
    def _validate_page_range(page_range: Tuple[int, int]) -> None:
        """
        Проверка корректности диапазона страниц.
        """

        if not isinstance(page_range, tuple) or len(page_range) != 2:
            raise TypeError("page_range должен быть кортежем (start, end)")

        start, end = page_range

        if not isinstance(start, int) or not isinstance(end, int):
            raise TypeError("start и end должны быть int")

        if start <= 0 or end <= 0:
            raise ValueError("Номера страниц должны быть > 0")

        if start > end:
            raise ValueError("start не может быть больше end")
