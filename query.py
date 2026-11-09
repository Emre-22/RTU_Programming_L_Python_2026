"""Flight database query validation and matching."""

from __future__ import annotations

import math

from validator import parse_datetime

RECORD_KEYS = {
    "flight_id",
    "origin",
    "destination",
    "departure_datetime",
    "arrival_datetime",
    "price",
}
QUERY_KEYS = RECORD_KEYS | {"min_price", "sort_by", "order", "limit"}
_STRING_FILTERS = {
    "flight_id",
    "origin",
    "destination",
    "departure_datetime",
    "arrival_datetime",
}
_NUMERIC_FILTERS = {"price", "min_price"}


def _valid_number(value: object) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    return isinstance(value, float) and math.isfinite(value)


def _valid_query(query: object) -> bool:
    if not isinstance(query, dict):
        return False
    if any(key not in QUERY_KEYS for key in query):
        return False

    for key in _STRING_FILTERS:
        if key not in query:
            continue
        value = query[key]
        if not isinstance(value, str):
            return False
        if key in {"departure_datetime", "arrival_datetime"}:
            if parse_datetime(value) is None:
                return False

    for key in _NUMERIC_FILTERS:
        if key in query and not _valid_number(query[key]):
            return False

    if "sort_by" in query:
        if not isinstance(query["sort_by"], str) or query["sort_by"] not in RECORD_KEYS:
            return False

    if "order" in query:
        order = query["order"]
        if "sort_by" not in query or not isinstance(order, str) or order not in {"asc", "desc"}:
            return False

    if "limit" in query:
        limit = query["limit"]
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
            return False

    return True


def run_query(db: list[dict], query: dict) -> dict:
    """Return one query result, or an INVALID_QUERY response."""
    if not _valid_query(query):
        return {"query": query, "error": "INVALID_QUERY", "matches": []}

    matches = []
    for flight in db:
        if any(flight.get(key) != query[key] for key in ("flight_id", "origin", "destination") if key in query):
            continue
        if "departure_datetime" in query and flight["departure_datetime"] < query["departure_datetime"]:
            continue
        if "arrival_datetime" in query and flight["arrival_datetime"] > query["arrival_datetime"]:
            continue
        if "price" in query and flight["price"] > query["price"]:
            continue
        if "min_price" in query and flight["price"] < query["min_price"]:
            continue
        matches.append(flight)

    if "sort_by" in query:
        matches = sorted(
            matches,
            key=lambda flight: flight[query["sort_by"]],
            reverse=query.get("order", "asc") == "desc",
        )

    if "limit" in query:
        matches = matches[: query["limit"]]

    return {"query": query, "matches": matches}


def run_queries(db: list[dict], queries: dict | list) -> list[dict]:
    """Run one query or a list of queries and return one response per query."""
    if isinstance(queries, dict):
        query_list = [queries]
    elif isinstance(queries, list):
        query_list = queries
    else:
        raise TypeError("queries must be a query object or a list of query objects")
    return [run_query(db, query) for query in query_list]

