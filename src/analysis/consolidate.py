"""Konsolidacja surowych obserwacji trip_updates do jednej wartości
na parę (kurs, przystanek). Wybór ostatniej obserwacji jako przybliżenia
wartości zrealizowanej.

Dodatkowo oznacza pary, dla których ostatnia obserwacja nastąpiła długo
po planowym czasie przyjazdu (sygnał błędu po stronie ZTP).
"""

import duckdb
import pandas as pd
from pathlib import Path

from .io import trip_updates_glob, READ_PARQUET_OPTS


def consolidate_trip_updates(raw_path: Path, feed: str, dates: list[str] | None = None) -> pd.DataFrame:
    """Zwraca jeden wiersz na (date, trip_id, stop_id): ostatnią znaną
    obserwację (opóźnienie, route_id, stop_sequence) i metadane konsolidacji.

    Parametry:
        raw_path: ścieżka do katalogu raw/
        feed: który feed konsolidować
        dates: opcjonalna lista dat w formacie 'YYYY-MM-DD' do zawężenia;
               None -> wszystkie dostępne dni w raw_path
    """
    wzorzec = trip_updates_glob(raw_path)

    filtr_dat = ""
    if dates:
        lista = ", ".join(f"'{d}'" for d in dates)
        filtr_dat = f"AND date IN ({lista})"

    zapytanie = f"""
        SELECT
            date,
            trip_id,
            stop_id,
            arg_max(route_id, observed_at)        AS route_id,
            arg_max(stop_sequence, observed_at)   AS stop_sequence,
            arg_max(arrival_delay, observed_at)   AS arrival_delay,
            arg_max(departure_delay, observed_at) AS departure_delay,
            arg_max(arrival_time, observed_at)    AS arrival_time,
            count(*)                              AS liczba_obserwacji,
            max(observed_at)                      AS ostatnia_obserwacja,
            (max(observed_at) - arg_max(arrival_time, observed_at)) > 7200 AS niepewny_kurs
        FROM read_parquet('{wzorzec}', {READ_PARQUET_OPTS})
        WHERE feed = '{feed}' {filtr_dat}
        GROUP BY date, trip_id, stop_id
        """
    return duckdb.query(zapytanie).to_df()