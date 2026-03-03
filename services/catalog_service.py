import os
from pathlib import Path
from typing import List, Optional, Tuple

from dotenv import load_dotenv

from core.exporter import ExcelExporter
from core.normalizer import CatalogNormalizer
from core.parser import CatalogParser
from core.pdf_processor import PDFProcessor
from core.vision_client import VisionClient

load_dotenv()


class CatalogService:
    """
    Оркестратор обработки каталога.

    Отвечает за:
    - загрузку страниц PDF
    - вызов Vision для каждой страницы
    - валидацию данных
    - нормализацию
    - экспорт в Excel
    """

    def __init__(
        self,
        input_pdf: str,
        output_file: str,
        prompt_path: str,
    ) -> None:
        self.input_pdf = Path(input_pdf).resolve()
        self.output_file = Path(output_file).resolve()

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

        :param page_range: диапазон страниц (start, end)
        """

        images = self.pdf_processor.convert_to_images(
            self.input_pdf,
            page_range=(22, 23),
        )

        all_raw_rows: List[dict] = []

        for page_number, image_bytes in images:
            print(f"Обработка страницы {page_number}")

            raw_rows = self.vision_client.extract_table_from_image(
                image_bytes
            )

            all_raw_rows.extend(raw_rows)

        if not all_raw_rows:
            raise ValueError("Не удалось получить данные из PDF")

        validated = self.parser.validate(all_raw_rows)
        normalized = self.normalizer.expand_alloys(validated)

        self.exporter.export(normalized, self.output_file)


        print(f"Готово. Сохранено: {self.output_file}")