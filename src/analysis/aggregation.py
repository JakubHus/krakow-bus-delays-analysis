"""Agregacja przyrostu opóźnienia na odcinkach międzyprzystankowych,
w oknach czasowych (dzień roboczy/weekend i pora dnia).
"""

import pandas as pd

MIN_OBSERVATIONS = 5


def build_segment_pairs(df: pd.DataFrame, delay_column: str = "arrival_delay") -> pd.DataFrame:
    """Dla każdego kursu (date, trip_id), posortowanego po stop_sequence, tworzy
    wiersz na każdy odcinek: (prev_stop_id, next_stop_id, increment, czas_lokalny
    końca odcinka). To jednostka przestrzenna dla dalszej agregacji. Nie jest to pojedynczy
    przystanek, tylko para sąsiadujących przystanków.

    Pomija wiersze bez stop_sequence oraz oznaczone jako
    extreme/uncertain, które znikształcałyby medianę pojedynczych, nielicznych
    odcinków.

    :param df: wynik build_prepared_dataset, po przejściu przez classify_time_window
    :param delay_column: nazwa kolumny z opóźnieniem
    """
    clean = df[
        df["stop_sequence"].notna()
        & ~df["arrival_delay_extreme"]
        & ~df["uncertain_completion"]
    ].copy()

    clean = clean.sort_values(["date", "trip_id", "stop_sequence"])
    clean["prev_stop_id"] = clean.groupby(["date", "trip_id"])["stop_id"].shift(1)
    clean["increment"] = clean[f"{delay_column}_increment"]

    segments = clean.dropna(subset=["prev_stop_id", "increment"]).copy()
    segments = segments.rename(columns={"stop_id": "next_stop_id"})
    return segments[["date", "trip_id", "route_id", "prev_stop_id", "next_stop_id",
                     "increment", "day_type", "time_of_day"]]


def aggregate_by_segment(segments: pd.DataFrame, min_observations: int = MIN_OBSERVATIONS) -> pd.DataFrame:
    """Agreguje przyrost opóźnienia po (prev_stop_id, next_stop_id, day_type, time_of_day):
    mediana, P85, P95, liczba obserwacji. Grupy poniżej min_observations są odrzucane.

    :param segments: wynik build_segment_pairs
    :param min_observations: minimalna liczba obserwacji w grupie (domyślnie 5)
    """
    grouped = segments.groupby(["prev_stop_id", "next_stop_id", "day_type", "time_of_day"])["increment"]
    result = grouped.agg(
        median_increment="median",
        p85_increment=lambda s: s.quantile(0.85),
        p95_increment=lambda s: s.quantile(0.95),
        observation_count="count",
    ).reset_index()
    return result[result["observation_count"] >= min_observations].reset_index(drop=True)