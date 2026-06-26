"""Decimal based Korean number parsing and validation helpers."""

import re
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ParsedNumber:
    raw: str
    value: Decimal
    unit: str


NUMBER_RE = re.compile(r"(?P<num>\d[\d,]*(?:\.\d+)?)\s*(?P<unit>억원|만원|천만\s*원|천만원|원|%)?")


def parse_number(text: str) -> ParsedNumber | None:
    """Parse common Korean budget and percent expressions without float."""

    normalized = text.strip()
    match = NUMBER_RE.search(normalized)
    if not match:
        return None
    raw_number = match.group("num").replace(",", "")
    value = Decimal(raw_number)
    unit = (match.group("unit") or "").replace(" ", "")
    if unit == "억원":
        value *= Decimal("100000000")
        unit = "원"
    elif unit in {"만원"}:
        value *= Decimal("10000")
        unit = "원"
    elif unit in {"천만원", "천만원"}:
        value *= Decimal("10000000")
        unit = "원"
    elif unit == "%":
        unit = "%"
    else:
        unit = "원" if "원" in normalized else unit
    return ParsedNumber(raw=text, value=value, unit=unit)

