"""
justetf.py — Scraping e processamento degli ETF da JustETF.

Cosa fa
-------
Scarica il catalogo degli ETF europei da JustETF.com usando la libreria
justetf-scraping (4364+ ETF con 42 colonne di dati).

Estrae l'indice di riferimento dal NOME dell'ETF (non da una descrizione).
Esempio: "iShares Core S&P 500 UCITS ETF USD (Acc)" → index = "S&P 500"
"""

from __future__ import annotations

import logging
import re
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def load_justetf_overview() -> Optional[pd.DataFrame]:
    """Scarica il catalogo degli ETF da JustETF (4364+ ETF, 42 colonne).

    Ritorna un DataFrame con:
    - Identificatori: wkn, ticker, valor, name, isin (indice)
    - Info: inception_date, age_in_years, strategy, domicile_country, currency, ter, ecc.
    - Performance: rendimenti ultimi giorni/settimane/mesi/anni (last_week, last_year, ecc.)
    - Volatilità: volatilità e max drawdown a 1/3/5 anni
    - Return per risk: metriche di performance aggiustate per il rischio
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
            "Installa con: pip install 'justetf-scraping @ git+https://github.com/druzsan/justetf-scraping.git'"
        )
        return None
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Errore nello scraping JustETF: {exc}")
        return None


def extract_index_from_name(etf_name: str) -> str:
    """Estrae l'indice di riferimento dal NOME dell'ETF.

    Cerca pattern comuni nel nome:
    - "MSCI WORLD", "MSCI USA", "MSCI EMERGING MARKETS" (e varianti)
    - "S&P 500", "S&P 1000"
    - "FTSE 100", "FTSE All-World"
    - "Russell 2000"
    - "Nasdaq 100", "Nasdaq 150"
    - "Nikkei 225"
    - "DAX", "CAC 40", "IBEX 35", "Stoxx", ecc.

    Esempio:
        "iShares Core S&P 500 UCITS ETF USD (Acc)" → "S&P 500"
        "Vanguard FTSE All-World UCITS ETF" → "FTSE All-World"
        "iShares MSCI WORLD UCITS ETF" → "MSCI WORLD"

    Se non trova pattern, ritorna "N/A".
    """
    if not isinstance(etf_name, str) or not etf_name:
        return "N/A"

    # Pattern ordinati per specificità (piu specifici per primi)
    patterns = [
        # MSCI varianti (solo MSCI + parola principale, non UCITS/ETF/ecc.)
        r"(MSCI\s+(?:ACWI|World|USA|China|EM|Emerging\s+Markets|Europe|Japan|AC\s+\w+))\b",
        # S&P (numero seguito opzionalmente da parola)
        r"(S&P\s+\d+)\b",
        # FTSE (numero o parole successive)
        r"(FTSE\s+(?:\d+|[\w\-]+))\b",
        # Russell (numero)
        r"(Russell\s+\d+)\b",
        # Nasdaq
        r"(Nasdaq\s+\d+)\b",
        # Nikkei
        r"(Nikkei\s+\d+)\b",
        # Stoxx Europa
        r"(Stoxx\s+(?:Europe\s+)?[\w\s]*)\b",
        # Indici europei principali
        r"\b(DAX|CAC\s+40|IBEX\s+35|AEX|OMX)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, etf_name, re.IGNORECASE)
        if match:
            index = match.group(1).strip()
            # Normalizza spazi multipli
            index = " ".join(index.split())
            return index

    return "N/A"


def add_index_column(df: pd.DataFrame, name_col: str = "name") -> pd.DataFrame:
    """Aggiunge una colonna 'index' estraendo l'indice dal nome dell'ETF."""
    result = df.copy()
    if name_col in result.columns:
        result["index"] = result[name_col].apply(extract_index_from_name)
    else:
        logger.warning(f"Colonna '{name_col}' non trovata. Creo colonna index con N/A")
        result["index"] = "N/A"
    return result


def prepare_export(df: pd.DataFrame) -> pd.DataFrame:
    """Prepara il DataFrame per l'export CSV.

    Mette 'index' all'inizio, poi tutte le altre colonne in ordine.
    """
    result = df.copy()

    # Se 'index' non c'è, creala
    if "index" not in result.columns:
        result = add_index_column(result)

    # Riordina: index first, poi tutto il resto
    cols = ["index"] + [c for c in result.columns if c != "index"]
    return result[cols]
