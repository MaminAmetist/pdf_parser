from pathlib import Path

from services.catalog_service import CatalogService


def main() -> None:
    BASE_DIR = Path(__file__).parent.resolve()

    input_pdf = BASE_DIR / "input" / "Deskar_compressed.pdf"
    output_xlsx = BASE_DIR / "output" / "result.xlsx"
    prompt_path = BASE_DIR / "prompts" / "catalog_prompt.txt"
    service = CatalogService(
        input_pdf=input_pdf,
        output_file=output_xlsx,
        prompt_path=prompt_path
    )
    service.process()


if __name__ == "__main__":
    main()
