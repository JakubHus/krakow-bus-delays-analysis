"""Odtwarzanie stop_sequence z rozkladu statycznego dla par
(trip_id, stop_id), dla ktorych brakuje go w danych.
"""

import io
import tempfile
import zipfile
from pathlib import Path

import duckdb
import pandas as pd


def build_feed_info_index(static_path: Path, feed: str) -> pd.DataFrame:
    """Buduje indeks wersji rozkładu statycznego dla danego feedu, czyli określa,
    który plik zip obowiązuje w jakim przedziale dat.

    Zwraca DataFrame: zip_name, feed_start_date, feed_end_date, feed_version
    (daty jako pandas Timestamp), posortowany chronologicznie.
    """
    rows = []
    for path in sorted(static_path.glob(f"GTFS_KRK_{feed}_*.zip")):
        with zipfile.ZipFile(path) as zf:
            text = zf.read("feed_info.txt").decode("utf-8")
        row = pd.read_csv(io.StringIO(text), dtype=str).iloc[0]
        rows.append({
            "zip_name": path.name,
            "feed_start_date": pd.to_datetime(row["feed_start_date"], format="%Y%m%d"),
            "feed_end_date": pd.to_datetime(row["feed_end_date"], format="%Y%m%d"),
            "feed_version": row["feed_version"],
        })
    return pd.DataFrame(rows).sort_values("feed_start_date").reset_index(drop=True)


def find_version_for_date(index: pd.DataFrame, date) -> str:
    """Zwraca nazwę pliku zip wersji rozkładu obowiązującej w danym dniu.

    :param index: wynik build_feed_info_index
    :param date: data (str lub pandas Timestamp)
    """
    date = pd.to_datetime(date)
    matching = index[(index["feed_start_date"] <= date) & (index["feed_end_date"] >= date)]
    if matching.empty:
        raise ValueError(f"Brak wersji rozkladu obejmujacej date {date.date()}")
    return matching.sort_values("feed_start_date").iloc[-1]["zip_name"]


def load_stop_sequences(static_path: Path, zip_name: str) -> pd.DataFrame:
    """Wczytuje stop_times.txt z danej paczki: unikalne (trip_id, stop_id, stop_sequence).

    :param static_path: ścieżka do katalogu static/
    :param zip_name: nazwa pliku zip (z find_version_for_date)
    """
    zip_path = static_path / zip_name
    with tempfile.TemporaryDirectory() as tmp_dir:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extract("stop_times.txt", path=tmp_dir)
        file_path = Path(tmp_dir) / "stop_times.txt"
        raw = duckdb.query(f"""
                SELECT DISTINCT
                    trip_id,
                    CAST(stop_id AS VARCHAR) AS stop_id,
                    stop_sequence AS stop_sequence_schedule
                FROM read_csv_auto('{file_path.as_posix()}')
            """).to_df()

    key_counts = raw.groupby(["trip_id", "stop_id"]).size()
    ambiguous_keys = set(key_counts[key_counts > 1].index)
    is_ambiguous = raw.set_index(["trip_id", "stop_id"]).index.isin(ambiguous_keys)
    return raw[~is_ambiguous].reset_index(drop=True)


def fill_stop_sequence(consolidated: pd.DataFrame, static_path: Path, feed: str) -> pd.DataFrame:
    """Uzupełnia brakujące stop_sequence, łącząc po (trip_id, stop_id) z rozkładem
    właściwym dla każdego dnia osobno, bo dni mogą mieć różne wersje rozkładu.

    Istniejące, niepuste wartości stop_sequence z danych RT nie są nadpisywane.

    :param consolidated: wynik consolidate_trip_updates
    :param static_path: ścieżka do katalogu static/
    :param feed: który feed
    """
    index = build_feed_info_index(static_path, feed)
    parts = []
    for date, group in consolidated.groupby("date"):
        zip_name = find_version_for_date(index, date)
        schedule = load_stop_sequences(static_path, zip_name)
        merged = group.merge(schedule, on=["trip_id", "stop_id"], how="left")
        merged["stop_sequence"] = merged["stop_sequence"].fillna(merged["stop_sequence_schedule"])
        parts.append(merged.drop(columns=["stop_sequence_schedule"]))
    return pd.concat(parts, ignore_index=True)