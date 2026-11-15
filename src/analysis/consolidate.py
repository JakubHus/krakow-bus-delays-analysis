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
    path_pattern = trip_updates_glob(raw_path)

    date_filter = ""
    if dates:
        date_list = ", ".join(f"'{d}'" for d in dates)
        date_filter = f"AND date IN ({date_list})"

    query = f"""
        SELECT
            date,
            trip_id,
            stop_id,
            arg_max(route_id, observed_at)        AS route_id,
            arg_max(stop_sequence, observed_at)   AS stop_sequence,
            arg_max(arrival_delay, observed_at)   AS arrival_delay,
            arg_max(departure_delay, observed_at) AS departure_delay,
            arg_max(arrival_time, observed_at)    AS arrival_time,
            count(*)                              AS observation_count,
            max(observed_at)                      AS last_observed_at,
            (max(observed_at) - arg_max(arrival_time, observed_at)) > 7200 AS uncertain_completion
        FROM read_parquet('{path_pattern}', {READ_PARQUET_OPTS})
        WHERE feed = '{feed}' {date_filter}
        GROUP BY date, trip_id, stop_id
        """
    return duckdb.query(query).to_df()