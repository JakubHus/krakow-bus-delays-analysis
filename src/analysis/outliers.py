"""Identyfikacja outlierów."""

import pandas as pd


EXTREME_DELAY_THRESHOLD = 7200


def flag_extreme_delay(df: pd.DataFrame, delay_column: str = "arrival_delay",
                       threshold: int = EXTREME_DELAY_THRESHOLD) -> pd.DataFrame:
    """Dodaje kolumnę <delay_column>_extreme: True gdy |delay| > threshold.

    Tylko oznacza, a nie usuwa. Decyzja o wykluczeniu z konkretnej analizy należy
    do etapu agregacji.

    :param df: ramka danych z kolumną delay_column
    :param delay_column: nazwa kolumny z opóźnieniem (domyślnie arrival_delay)
    :param threshold: prog w sekundach (domyślnie 7200 = 2h)
    """
    result = df.copy()
    result[f"{delay_column}_extreme"] = result[delay_column].abs() > threshold
    return result