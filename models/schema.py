from typing import Optional

from pydantic import BaseModel, Field


class CatalogRow(BaseModel):
    """
    Строка каталога после распознавания.
    """

    model: str = Field(..., min_length=3)
    L: float
    I_C: float
    S: float
    d: float
    r: float
    P: Optional[str] = None
    M: Optional[str] = None
    K: Optional[str] = None
