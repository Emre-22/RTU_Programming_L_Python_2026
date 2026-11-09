"""Command-line entry point for the flight query lab."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from datetime import datetime

from csv_loader import parse_files
from query import run_queries
from validator import load_airports

STUDENT_ID = "251ADB139"
FIRST_NAME = "Emre"
LAST_NAME = "Elaziz"


class _InputError(Exception):
    """Raised for malformed input files or input shapes."""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate flight CSV files and answer flight queries.")
    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument("-i", metavar="FILE", help="parse one CSV file")
    sources.add_argument("-d", metavar="FOLDER", help="parse CSV files in a folder")
    sources.add_argument("-j", metavar="FILE", help="load an existing JSON database")
    parser.add_argument("-a", metavar="FILE", help="airport list file (required with -i or -d)")
    parser.add_argument("-o", metavar="FILE", help="database output path (only with -i or -d)")
    parser.add_argument("-q", metavar="FILE", help="JSON query file")
    parser.add_argument("-r", metavar="FOLDER", default=".", help="query response folder (default: current directory)")
    return parser


def _load_json(path: str, description: str):
    try:
        with open(path, "r", encoding="utf-8") as json_file:
            return json.load(json_file)
    except OSError as exc:
        raise _InputError(f"cannot read {description} file '{path}': {exc}") from exc
    except json.JSONDecodeError as exc:
        raise _InputError(f"invalid JSON in {description} file '{path}': {exc.msg}") from exc


def _write_json(path: str, value: object) -> None:
    with open(path, "w", encoding="utf-8", newline="") as json_file:
        json.dump(value, json_file, ensure_ascii=False, indent=2)
        json_file.write("\n")


def _csv_paths(folder: str) -> list[str]:
    names = sorted(
        name
        for name in os.listdir(folder)
        if name.endswith(".csv") and os.path.isfile(os.path.join(folder, name))
    )
    if not names:
        raise _InputError(f"no .csv files found in folder '{folder}'")
    return [os.path.join(folder, name) for name in names]


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
        if (args.i is not None or args.d is not None) and args.a is None:
            parser.error("-a is required with -i and -d")
        if args.j is not None and args.o is not None:
            parser.error("-o may be used only with -i or -d")
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 0

    logger = logging.getLogger("flight_parser")
    previous_level = logger.level
    previous_propagate = logger.propagate
    handler: logging.FileHandler | None = None

    try:
        if args.i is not None or args.d is not None:
            database_path = args.o or "db.json"
            errors_path = os.path.join(
                os.path.dirname(os.path.abspath(database_path)), "errors.log"
            )
            logger.setLevel(logging.INFO)
            logger.propagate = False
            handler = logging.FileHandler(errors_path, mode="w", encoding="utf-8")
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)s %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )
            logger.addHandler(handler)

            airports = load_airports(args.a)
            paths = [args.i] if args.i is not None else _csv_paths(args.d)
            records, errors = parse_files(paths, airports)
            for error in errors:
                logger.warning("%s", error)
            _write_json(database_path, records)
            database = records
        else:
            database = _load_json(args.j, "database")
            if not isinstance(database, list) or any(not isinstance(row, dict) for row in database):
                raise _InputError("database JSON must be an array of objects")

        if args.q is not None:
            queries = _load_json(args.q, "query")
            if isinstance(queries, dict):
                pass
            elif isinstance(queries, list):
                pass
            else:
                raise _InputError("query JSON must be an object or an array of query objects")

            responses = run_queries(database, queries)
            response_name = (
                f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_"
                f"{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            )
            _write_json(os.path.join(args.r, response_name), responses)

        return 0
    except (_InputError, OSError, UnicodeError, csv.Error) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        if handler is not None:
            logger.removeHandler(handler)
            handler.close()
        logger.setLevel(previous_level)
        logger.propagate = previous_propagate


if __name__ == "__main__":
    sys.exit(main())
