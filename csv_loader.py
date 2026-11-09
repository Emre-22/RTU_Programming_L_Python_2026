"""CSV file discovery and flight-record loading for the flight query lab."""

from __future__ import annotations

import csv
import os

from validator import to_record, validate_row


def parse_files(paths: list[str], airports: set[str]) -> tuple[list[dict], list[str]]:
    """Parse files in the supplied order, returning records and row errors."""
    records: list[dict] = []
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()

    for path in paths:
        path_text = os.fspath(path)
        file_name = path_text.replace("\\", "/").rsplit("/", 1)[-1]

        with open(path_text, "r", encoding="utf-8", newline="") as csv_file:
            for line_number, physical_line in enumerate(csv_file, start=1):
                if line_number == 1:
                    # The first physical line is always the header.
                    continue

                line = physical_line.rstrip("\r\n")
                if not line.strip() or line.lstrip().startswith("#"):
                    continue

                fields = next(csv.reader([line]))
                error_code = validate_row(fields, airports)
                if error_code is not None:
                    errors.append(
                        f"{file_name}:{line_number}: {error_code} | {line}"
                    )
                    continue

                stripped = [field.strip() for field in fields]
                duplicate_key = (stripped[0], stripped[3])
                if duplicate_key in seen:
                    errors.append(
                        f"{file_name}:{line_number}: DUPLICATE_FLIGHT | {line}"
                    )
                    continue

                seen.add(duplicate_key)
                records.append(to_record(fields))

    return records, errors


