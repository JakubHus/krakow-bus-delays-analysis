"""Konwersja czasu z UTC na czas lokalny."""

import pandas as pd

WARSAW_TZ = "Europe/Warsaw"


def to_local_time(epoch_seconds: pd.Series, tz: str = WARSAW_TZ) -> pd.Series:
    """Konwertuje kolumnę epoch (sekundy UTC) na czas lokalny.

    Efekt uboczny zmiany czasu w tym kierunku to, że w noc zmiany na czas zimowy
    godzina lokalna 02:00-03:00 odpowiada dwom różnym momentom UTC (wystąpiła
    faktycznie dwa razy)

    :param epoch_seconds: kolumna z epoch (sekundy UTC), int lub float
    :param tz: strefa docelowa (domyślnie Europe/Warsaw)
    """
    return pd.to_datetime(epoch_seconds, unit="s", utc=True).dt.tz_convert(tz)


def add_local_columns(df: pd.DataFrame, epoch_column: str, prefix: str | None = None,
                      tz: str = WARSAW_TZ) -> pd.DataFrame:
    """Dodaje do dataframe kolumny pochodne od epoch_column, przeliczone na czas lokalny:
    <prefix>_local (pełny znacznik czasu ze strefy), <prefix>_date_local,
    <prefix>_hour_local, <prefix>_weekday_local (0 -> poniedziałek).

    Nie modyfikuje oryginalnej kolumny epoch, tylko zwraca kopie dataframe z nowymi kolumnami.

    :param df: dataframe zawierający epoch_column
    :param epoch_column: nazwa kolumny z epoch (np. "arrival_time")
    :param prefix: prefiks nowych kolumn (domyślnie: epoch_column)
    :param tz: strefa docelowa (domyślnie Europe/Warsaw)
    """
    prefix = prefix or epoch_column
    local = to_local_time(df[epoch_column], tz=tz)
    result = df.copy()
    result[f"{prefix}_local"] = local
    result[f"{prefix}_date_local"] = local.dt.date
    result[f"{prefix}_hour_local"] = local.dt.hour
    result[f"{prefix}_weekday_local"] = local.dt.weekday
    return result