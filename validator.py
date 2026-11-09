"""Airport and flight-row validation for the flight query lab."""

from __future__ import annotations

import math
import re
from datetime import datetime

FIELD_COUNT = 6
_DATE_FORMAT = "%Y-%m-%d %H:%M"
_DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}\Z")
_FLIGHT_ID_RE = re.compile(r"[A-Za-z0-9]{2,8}\Z")
_AIRPORT_RE = re.compile(r"[A-Z]{3}\Z")


def parse_datetime(value: str) -> datetime | None:
    """Parse only a real, zero-padded datetime in the required exact format."""
    if not isinstance(value, str) or _DATE_RE.fullmatch(value) is None:
        return None
    try:
        return datetime.strptime(value, _DATE_FORMAT)
    except ValueError:
        return None


def load_airports(path: str) -> set[str]:
    """Load exact, case-sensitive airport codes from a one-code-per-line file."""
    airports: set[str] = set()
    with open(path, "r", encoding="utf-8") as airport_file:
        for line in airport_file:
            code = line.strip()
            if not code or code.startswith("#"):
                continue
            airports.add(code)
    return airports


def validate_row(fields: list[str], airports: set[str]) -> str | None:
    """Return the first validation error code for one CSV row, if any."""
    if len(fields) != FIELD_COUNT:
        return "WRONG_FIELD_COUNT"

    values = [field.strip() for field in fields]
    if any(value == "" for value in values):
        return "MISSING_FIELD"

    flight_id, origin, destination, departure_text, arrival_text, price_text = values

    if _FLIGHT_ID_RE.fullmatch(flight_id) is None:
        return "INVALID_FLIGHT_ID"

    if _AIRPORT_RE.fullmatch(origin) is None or origin not in airports:
        return "INVALID_ORIGIN"

    if _AIRPORT_RE.fullmatch(destination) is None or destination not in airports:
        return "INVALID_DESTINATION"

    if origin == destination:
        return "SAME_ORIGIN_DESTINATION"

    departure = parse_datetime(departure_text)
    if departure is None:
        return "INVALID_DEPARTURE"

    arrival = parse_datetime(arrival_text)
    if arrival is None:
        return "INVALID_ARRIVAL"

    if arrival <= departure:
        return "ARRIVAL_NOT_AFTER_DEPARTURE"

    try:
        price = float(price_text)
    except (TypeError, ValueError, OverflowError):
        return "INVALID_PRICE"
    if not math.isfinite(price):
        return "INVALID_PRICE"
    if price <= 0:
        return "NON_POSITIVE_PRICE"

    return None


def to_record(fields: list[str]) -> dict:
    """Convert a valid row to the exact database record shape."""
    if len(fields) != FIELD_COUNT:
        raise ValueError("a flight row must contain exactly six fields")
    values = [field.strip() for field in fields]
    return {
        "flight_id": values[0],
        "origin": values[1],
        "destination": values[2],
        "departure_datetime": values[3],
        "arrival_datetime": values[4],
        "price": float(values[5]),
    }
