"""
etf_analysis.py — Analisi di portafogli equally weighted su ETF reali.

Estende la logica di equal_weight.py per usare serie storiche di ETF
scaricate da Yahoo Finance (invece che indici MSCI).
"""

from __future__ import annotations

from itertools import combinations
from math import comb
from typing import Callable, Iterable, Optional, Sequence

import numpy as np
import pandas as pd


def download_etf_prices(tickers: Sequence[str], period: str = "10y") -> pd.DataFrame:
    """Scarica i prezzi di chiusura di una lista di ETF da yfinance.

    Ritorna un DataFrame con una colonna per ticker, indice = Date.
    """
    try:
        import yfinance as yf

        data = yf.download(tickers, period=period, progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            # Se yfinance ritorna MultiIndex (multiple tickers), prendi solo Close
            prices = data["Close"]
        else:
            # Single ticker
            prices = data[["Close"]]
        prices.columns = [col if isinstance(col, str) else col[0] for col in prices.columns]
        return prices.sort_index().dropna(how="all")
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Errore nello scaricamento da yfinance: {exc}") from exc


def resample_to_monthly(prices: pd.DataFrame) -> pd.DataFrame:
    """Converte prezzi daily a mensile (fine mese)."""
    return prices.resample("ME", label="right").last().to_period("M")


def portfolio_yearly_returns(
    panel: pd.DataFrame, which: Sequence[str], months: int = 120
) -> tuple[float, float, int]:
    """(rendimento annualizzato, volatilita, n. osservazioni) di un EW su ETF."""
    cols = list(which)
    if not all(c in panel.columns for c in cols):
        raise ValueError(f"Colonne non trovate. Disponibili: {list(panel.columns)}")
    growth = (panel[cols] / panel[cols].shift(months)).mean(axis=1)
    ann_return = float(growth.mean() ** (12 / months) - 1)
    return ann_return, float(growth.std()), int(growth.count())


def evaluate_combinations(
    panel: pd.DataFrame,
    k: int,
    months: int = 120,
    universe: Optional[Iterable[str]] = None,
    progress: Optional[Callable[[int, int], None]] = None,
) -> pd.DataFrame:
    """Valuta tutte le combinazioni di k ETF come portafogli EW."""
    cols = list(universe) if universe is not None else list(panel.columns)
    if k < 1 or k > len(cols):
        raise ValueError(f"k={k} non valido per {len(cols)} ETF disponibili.")

    combos = list(combinations(cols, k))
    total = len(combos)
    index: list[str] = []
    rows: list[tuple[float, float, int]] = []

    for j, combo in enumerate(combos):
        index.append(", ".join(combo))
        try:
            rows.append(portfolio_yearly_returns(panel, combo, months))
        except Exception:  # noqa: BLE001
            rows.append((np.nan, np.nan, 0))
        if progress is not None and (j + 1) % 500 == 0:
            progress(j + 1, total)
    if progress is not None:
        progress(total, total)

    res = pd.DataFrame(rows, index=index, columns=["return", "vol", "valid"])
    res["sharpe"] = res["return"] / res["vol"]
    return res.dropna(subset=["return"])


def count_combinations(n_etfs: int, k: int) -> int:
    """Numero di combinazioni di k ETF su n."""
    return comb(n_etfs, k)


def summary_stats(panel: pd.DataFrame, window: int = 120) -> pd.DataFrame:
    """Statistiche di rendimento/rischio per ETF."""
    roll = panel.pct_change(window)
    years = window / 12.0
    median_ann = ((roll.median() + 1) ** (1 / years) - 1) * 100
    std = roll.std() * 100
    sharpe_like = median_ann / std

    out = pd.DataFrame(
        {
            "Rend. Medi (%)": (roll.mean() * 100).round(2),
            "DevStd (%)": std.round(2),
            "Mediana Ann. (%)": median_ann.round(2),
            "Sharpe-like": sharpe_like.round(3),
        }
    )
    return out.sort_values("DevStd (%)")


def correlation_matrix(panel: pd.DataFrame, change_months: int = 1) -> pd.DataFrame:
    """Matrice di correlazione dei rendimenti."""
    return panel.pct_change(change_months).corr()


def equal_weight_value(panel: pd.DataFrame, which: Sequence[str], base: float = 100.0) -> pd.Series:
    """Valore cumulato di un portafoglio EW su ETF."""
    temp = panel[list(which)].dropna()
    if temp.empty:
        return pd.Series(dtype=float)
    return (base * temp / temp.iloc[0]).mean(axis=1)


def rolling_return(panel: pd.DataFrame, which: Sequence[str], months: int = 120) -> pd.Series:
    """Rendimento rolling a `months` mesi del portafoglio EW."""
    temp = panel[list(which)].dropna()
    return temp.pct_change(periods=months, fill_method=None).mean(axis=1).dropna()
