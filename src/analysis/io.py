"""Pomocnicze funkcje do odczytu surowych danych GTFS-RT."""

from pathlib import Path


def trip_updates_glob(raw_path: Path, feed: str | None = None) -> str:
    """Buduje wzorzec ścieżki do plików trip_updates, gotowy dla read_parquet.

    Zwraca sam string ze ścieżką, nie samo zapytanie SQL.
    Dzięki temu funkcja jest uniwersalna. Ten sam wzorzec pasuje
    do SELECT, DESCRIBE czy dowolnego innego zapytania na tych danych.
    """
    return f"{raw_path.as_posix()}/trip_updates/**/*.parquet"


READ_PARQUET_OPTS = "hive_partitioning = true, union_by_name = true"