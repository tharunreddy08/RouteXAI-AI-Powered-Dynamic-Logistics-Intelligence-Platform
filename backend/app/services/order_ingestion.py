"""
Parses uploaded CSV/JSON order files into validated order rows.
Row-level errors are collected rather than aborting the whole upload, so a
handful of bad rows don't block the rest of a batch.
"""
import csv
import io
import json
from typing import List, Tuple

from pydantic import ValidationError

from app.schemas.order import OrderCreate


def parse_csv(content: bytes) -> Tuple[List[OrderCreate], List[str]]:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows: List[OrderCreate] = []
    errors: List[str] = []

    for i, raw_row in enumerate(reader, start=2):  # header is row 1
        try:
            cleaned = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in raw_row.items() if k}
            if "latitude" in cleaned and cleaned["latitude"] not in (None, ""):
                cleaned["latitude"] = float(cleaned["latitude"])
            if "longitude" in cleaned and cleaned["longitude"] not in (None, ""):
                cleaned["longitude"] = float(cleaned["longitude"])
            if "package_weight" in cleaned and cleaned["package_weight"] not in (None, ""):
                cleaned["package_weight"] = float(cleaned["package_weight"])
            # Drop empty-string optional fields so schema defaults apply.
            cleaned = {k: v for k, v in cleaned.items() if v != ""}
            rows.append(OrderCreate(**cleaned))
        except (ValidationError, ValueError, TypeError) as e:
            errors.append(f"Row {i}: {e}")

    return rows, errors


def parse_json(content: bytes) -> Tuple[List[OrderCreate], List[str]]:
    rows: List[OrderCreate] = []
    errors: List[str] = []

    try:
        data = json.loads(content.decode("utf-8"))
    except json.JSONDecodeError as e:
        return [], [f"Invalid JSON: {e}"]

    if isinstance(data, dict):
        data = data.get("orders", [data])

    if not isinstance(data, list):
        return [], ["JSON payload must be a list of orders or {'orders': [...]}."]

    for i, raw_row in enumerate(data, start=1):
        try:
            rows.append(OrderCreate(**raw_row))
        except (ValidationError, TypeError) as e:
            errors.append(f"Item {i}: {e}")

    return rows, errors
