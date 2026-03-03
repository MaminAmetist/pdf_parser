import io
from pathlib import Path
from typing import List, Tuple, Optional

from PIL import Image
from pdf2image import convert_from_path


class PDFProcessor:
    """
    PDF → список PNG-страниц (bytes) с номерами страниц.
    """

    def __init__(self, dpi: int = 300) -> None:
        """
        :param dpi: разрешение рендера страниц
        """
        if dpi <= 0:
            raise ValueError("dpi должен быть > 0")

        self._dpi: int = dpi

    def convert_to_images(
            self,
            pdf_path: Path,
            page_range: Optional[Tuple[int, int]] = None,
    ) -> List[Tuple[int, bytes]]:
        """
        Конвертация PDF в PNG-страницы.

        :param pdf_path: путь к PDF-файлу
        :param page_range: (start, end) — диапазон страниц, 1-indexed
        :return: список кортежей (номер_страницы, PNG bytes)
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"{pdf_path} не найден")

        first_page: Optional[int] = None
        last_page: Optional[int] = None

        if page_range:
            start, end = page_range

            if start <= 0 or end <= 0:
                raise ValueError("Нумерация страниц начинается с 1")

            if start > end:
                raise ValueError("start не может быть больше end")

            first_page = start
            last_page = end

        pages: List[Image.Image] = convert_from_path(
            str(pdf_path),
            dpi=self._dpi,
            first_page=first_page,
            last_page=last_page,
        )

        if not pages:
            raise ValueError("PDF пустой или не читается")

        result: List[Tuple[int, bytes]] = []

        # если диапазон задан — нумерация начинается с start
        current_page = page_range[0] if page_range else 1

        for page in pages:
            buffer = io.BytesIO()
            page.save(buffer, format="PNG")
            result.append((current_page, buffer.getvalue()))
            current_page += 1

        return result
