"""Klasyfikacja obserwacji na okna czasowe: dzień roboczy/weekend, pora dnia."""

import pandas as pd

MORNING_PEAK = range(6, 9)      # 6:00-8:59
EVENING_PEAK = range(15, 18)    # 15:00-17:59


def classify_time_window(df: pd.DataFrame, hour_column: str = "arrival_hour_local",
                         weekday_column: str = "arrival_weekday_local") -> pd.DataFrame:
    """Dodaje kolumny day_type (weekday lub weekend) i time_of_day (morning_peak,
    evening_peak lub off_peak), na podstawie godziny i dnia tygodnia w czasie lokalnym.

    :param df: ramka z kolumnami hour_column, weekday_column
    :param hour_column: nazwa kolumny z godzina lokalna (0-23)
    :param weekday_column: nazwa kolumny z dniem tygodnia (0=poniedziałek, 6=niedziela)
    """
    result = df.copy()
    result["day_type"] = result[weekday_column].apply(
        lambda w: "weekend" if w in (5, 6) else "weekday"
    )
    result["time_of_day"] = result[hour_column].apply(_classify_hour)
    return result


def _classify_hour(hour: float) -> str:
    if pd.isna(hour):
        return pd.NA
    hour = int(hour)
    if hour in MORNING_PEAK:
        return "morning_peak"
    if hour in EVENING_PEAK:
        return "evening_peak"
    return "off_peak"