"""Przyrost opóźnienia na odcinku, czyli różnica opóźnienia między kolejnymi
przystankami tego samego kursu (niekoniecznie każdym
przystankiem rozkładowym, jeśli któryś nie został zarejestrowany
przez RT, odcinek jest po prostu dłuższy, a nie błędny).
"""

import pandas as pd
import numpy as np


def compute_delay_increment(df: pd.DataFrame, delay_column: str = "arrival_delay") -> pd.DataFrame:
    """Dla każdego kursu (date, trip_id), posortowanego po stop_sequence, liczy
    różnice delay_column względem poprzedniego przystanku.

    Wiersze bez stop_sequence nie moga byc
    jednoznacznie uporządkowane w ramach kursu, więc dostają 'increment = NaN'
    i nie wpływają na obliczenia dla pozostałych przystanków tego kursu.

    :param df: ramka z kolumnami date, trip_id, stop_sequence, delay_column
    :param delay_column: nazwa kolumny z opóźnieniem
    """
    has_sequence = df[df["stop_sequence"].notna()].copy()
    no_sequence = df[df["stop_sequence"].isna()].copy()

    has_sequence = has_sequence.sort_values(["date", "trip_id", "stop_sequence"])
    has_sequence[f"{delay_column}_increment"] = (
        has_sequence.groupby(["date", "trip_id"])[delay_column].diff()
    )
    no_sequence[f"{delay_column}_increment"] = np.nan

    result = pd.concat([has_sequence, no_sequence], ignore_index=True)
    result[f"{delay_column}_increment"] = result[f"{delay_column}_increment"].astype("float64")
    return result