"""
justetf.py — Scraping e processamento degli ETF da JustETF.

Cosa fa
-------
Scarica il catalogo degli ETF europei da JustETF.com usando la libreria
justetf-scraping, estrae le info principali (nome, ISIN, TER, underlying index,
asset class) e le trasforma in un DataFrame pandas pronto per l'analisi.

JustETF è il principale repository europeo di dati sugli ETF: quotazioni reali,
holdings, fee, valutazioni ecc. Questo modulo ne estrae il catalogo e lo allinea
ai ticker Yahoo Finance quando possibile.
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def load_justetf_overview(timeout: int = 30) -> Optional[pd.DataFrame]:
    """Scarica il catalogo degli ETF da JustETF.

    Ritorna un DataFrame con colonne: name, isin, ter, type, region, ecc.
    Se lo scraping fallisce, ritorna None e loga l'errore.

    `timeout` = secondi di attesa per la connessione.
    """
    try:
        import justetf_scraping

        logger.info("Scarico catalogo ETF da JustETF.com…")
        etfs = justetf_scraping.load_overview()

        if etfs is None or etfs.empty:
            logger.warning("load_overview ha ritornato DataFrame vuoto.")
            return None

        logger.info(f"Caricati {len(etfs)} ETF da JustETF.")
        return etfs

    except ImportError:
        logger.error(
            "justetf-scraping non installato. "
            "Installa con: pip install 'justetf-scraping[all]@git+https://github.com/druzsan/justetf-scraping.git'"
        )
        return None
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Errore nello scraping JustETF: {exc}")
        return None


def filter_etfs(
    df: pd.DataFrame,
    ter_max: Optional[float] = None,
    region: Optional[str] = None,
    asset_class: Optional[str] = None,
) -> pd.DataFrame:
    """Filtra il catalogo ETF per TER, regione, asset class."""
    result = df.copy()
    if ter_max is not None:
        result = result[result.get("ter", float("inf")) <= ter_max]
    if region is not None:
        result = result[result.get("region", "").str.contains(region, case=False, na=False)]
    if asset_class is not None:
        result = result[result.get("asset_class", "").str.contains(asset_class, case=False, na=False)]
    return result


def resolve_yahoo_ticker(isin: str) -> Optional[str]:
    """Tenta di mappare un ISIN a un ticker Yahoo Finance.

    Logica semplice: chiama yfinance e verifica se l'ISIN valida.
    In un ambiente reale useresti una lookup table o un'API dedicata.
    """
    try:
        import yfinance as yf

        # Prova come ticker diretto (alcuni ISIN funzionano su yfinance)
        tick = yf.Ticker(isin)
        hist = tick.history(period="1d")
        if not hist.empty:
            return isin
    except Exception:  # noqa: BLE001
        pass
    return None


def add_yahoo_tickers(df: pd.DataFrame, name_col: str = "name") -> pd.DataFrame:
    """Prova a risolvere i ticker Yahoo Finance per ogni ETF (lento, usa una cache in produzione)."""
    result = df.copy()
    if "yahoo_ticker" not in result.columns:
        result["yahoo_ticker"] = result.get("isin", "").apply(resolve_yahoo_ticker)
    return result
