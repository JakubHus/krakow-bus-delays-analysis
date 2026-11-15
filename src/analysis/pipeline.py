"""Budowa gotowego, oczyszczonego zbioru analitycznego. Łączy kroki
1-5 preprocessingu w jedno wywołanie, żeby nie powielać tego samego
łańcucha w każdym etapie analizy.
"""

from pathlib import Path

import pandas as pd

from .consolidate import consolidate_trip_updates
from .schedule import fill_stop_sequence
from .localtime import add_local_columns
from .outliers import flag_extreme_delay
from .increments import compute_delay_increment


def build_prepared_dataset(raw_path: Path, static_path: Path, feed: str,
                           target_dates: list[str]) -> pd.DataFrame:
    """Zwraca gotowy skonsolidowany zbiór z uzupełnionym stop_sequence,
    czasem lokalnym, flagą wartości odstających i przyrostem opóźnienia.

    Ogranicza wynik do target_dates wg arrival_date_local.

    :param raw_path: ścieżka do katalogu raw/
    :param static_path: ścieżka do katalogu static/
    :param feed: który feed
    :param target_dates: lista dat 'YYYY-MM-DD' stanowiących docelowy zakres
    """
    consolidated = consolidate_trip_updates(raw_path, feed=feed)
    filled = fill_stop_sequence(consolidated, static_path, feed=feed)
    with_local = add_local_columns(filled, epoch_column="arrival_time", prefix="arrival")
    in_range = with_local[with_local["arrival_date_local"].astype(str).isin(target_dates)]
    flagged = flag_extreme_delay(in_range)
    return compute_delay_increment(flagged)