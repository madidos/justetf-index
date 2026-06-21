"""
justetf.py — Scraping e processamento degli ETF da JustETF.

Cosa fa
-------
Scarica il catalogo degli ETF europei da JustETF.com usando la libreria
justetf-scraping e estrae le info principali (nome, ISIN, TER, indice di
riferimento dalla descrizione).

JustETF è il principale repository europeo di dati sugli ETF.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def load_justetf_overview() -> Optional[pd.DataFrame]:
    """Scarica il catalogo degli ETF da JustETF.

    Ritorna un DataFrame con colonne: name, isin, ter, description, ecc.
    Se lo scraping fallisce, ritorna None e loga l'errore.
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


def extract_index_from_description(desc: str) -> str:
    """Estrae l'indice di riferimento dalla descrizione dell'ETF.

    Cerca pattern comuni: "MSCI WORLD", "S&P 500", "FTSE", ecc.
    Se non trova niente, ritorna "N/A".
    """
    if not isinstance(desc, str) or not desc:
        return "N/A"

    # Pattern comuni di indici
    patterns = [
        r"(MSCI\s+[\w\s]+(?:IMI|ESG)?)",
        r"(S&P\s+\d+)",
        r"(FTSE\s+[\w\s]+)",
        r"(Russell\s+[\w\d]+)",
        r"(Nikkei\s+\d+)",
        r"(DAX|CAC|IBEX)",
    ]

    for pattern in patterns:
        match = re.search(pattern, desc, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # Se non trova pattern, prova a estrarre le parole chiave principali
    # (probabilmente l'indice è menzionato all'inizio)
    words = desc.split()
    if len(words) >= 2:
        first_two = " ".join(words[:2]).strip()
        if any(keyword in first_two.upper() for keyword in ["MSCI", "S&P", "FTSE", "RUSSELL"]):
            return first_two

    return "N/A"


def add_index_column(df: pd.DataFrame, desc_col: str = "description") -> pd.DataFrame:
    """Aggiunge una colonna 'index' estraendo l'indice dalla descrizione."""
    result = df.copy()
    if desc_col in result.columns:
        result["index"] = result[desc_col].apply(extract_index_from_description)
    else:
        result["index"] = "N/A"
    return result


def prepare_export(df: pd.DataFrame) -> pd.DataFrame:
    """Prepara il DataFrame per l'export CSV con le colonne principali."""
    cols = []
    for col in ["name", "isin", "ter", "index"]:
        if col in df.columns:
            cols.append(col)

    if not cols:
        return df.copy()

    result = df[cols].copy()
    # Ordina per TER crescente
    if "ter" in result.columns:
        result = result.sort_values("ter")
    return result
