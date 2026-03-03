import base64
import json
import re
from pathlib import Path
from typing import List, Dict, Any

import httpx


class VisionClient:
    """
    Клиент OpenRouter для распознавания таблицы из изображения.

    Отвечает за:
    - загрузку промпта из файла
    - отправку изображения в модель
    - возврат JSON-структуры
    """
    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
            self,
            api_key: str,
            prompt_path: Path,
            model: str = "openai/gpt-4o",
            timeout: int = 1200,
    ) -> None:
        """
        :param api_key: API ключ OpenRouter
        :param prompt_path: путь к текстовому файлу с промптом
        :param model: модель с поддержкой vision
        :param timeout: таймаут запроса
        """
        if not api_key:
            raise ValueError("api_key обязателен")
        if not prompt_path.exists():
            raise FileNotFoundError(f"Промпт не найден: {prompt_path}")

        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._prompt = prompt_path.read_text(encoding="utf-8")

    def extract_table_from_image(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Отправляет изображение в OpenRouter и возвращает JSON-массив.

        :param image_bytes: изображение страницы в формате bytes
        :return: список словарей
        """

        if not image_bytes:
            raise ValueError("image_bytes пустой")

        encoded_image = base64.b64encode(image_bytes).decode()

        payload = {
            "model": self._model,
            "temperature": 0,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self._prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{encoded_image}"}
                        },
                    ],
                }
            ],
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(self.OPENROUTER_URL, headers=headers, json=payload)

            if response.status_code != 200:
                raise RuntimeError(f"OpenRouter error {response.status_code}: {response.text}")

            data = response.json()

            try:
                content = data["choices"][0]["message"]["content"]
            except (KeyError, IndexError) as exc:
                raise RuntimeError("Некорректная структура ответа модели") from exc

            return self._parse_json(content)

    @staticmethod
    def _parse_json(content: str) -> List[Dict[str, Any]]:
        """
        Парсинг JSON-ответа модели.
        Убирает возможные markdown-обёртки.
        """

        match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
        cleaned = match.group(1) if match else content

        try:
            parsed = json.loads(cleaned.strip())
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Модель вернула невалидный JSON: {exc}") from exc

        if not isinstance(parsed, list):
            raise RuntimeError(f"Ожидался JSON-массив, получено: {type(parsed)}")

        return parsed
