"""
app.py — Interfaccia web (Streamlit) per scaricare il catalogo ETF da JustETF.

Avvio:
    pip install -r requirements.txt
    streamlit run app.py

Si apre nel browser su http://localhost:8501
"""

from __future__ import annotations

import logging

import streamlit as st

import justetf as je

logging.basicConfig(level=logging.INFO)

st.set_page_config(page_title="JustETF Catalog", page_icon="📊", layout="wide")

st.title("📊 Catalogo ETF da JustETF")
st.caption(
    "Scarica il catalogo completo degli ETF europei da JustETF.com, "
    "con l'indice di riferimento estratto dalla descrizione."
)

# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("ℹ️ Informazioni")
    st.markdown(
        """
**Colonne:**
- **index** — indice di riferimento (estratto dalla descrizione)
- **name** — nome dell'ETF
- **isin** — codice ISIN
- **ter** — commissione annuale (%)

Dati aggiornati: JustETF.com
        """
    )


@st.cache_data(show_spinner=False, ttl=3600)
def cached_justetf_overview():
    return je.load_justetf_overview()


# --------------------------------------------------------------------------- #
# Caricamento ETF da JustETF
# --------------------------------------------------------------------------- #
if st.button("▶️ Avvia il download da JustETF.com", type="primary", use_container_width=True):
    with st.spinner("Scarico il catalogo da JustETF.com… (questo puo richiedere 1-2 minuti)"):
        etfs_raw = cached_justetf_overview()
    st.session_state.etfs_raw = etfs_raw
else:
    etfs_raw = st.session_state.get("etfs_raw")

if etfs_raw is None:
    st.info("👆 Clicca il bottone per avviare il download del catalogo ETF da JustETF.com")
    st.stop()

if etfs_raw.empty:
    st.error(
        "❌ Impossibile scaricare il catalogo da JustETF. "
        "Verifica che `justetf-scraping` sia installato.\n\n"
        "Installa con:\n"
        "`pip install 'justetf-scraping @ git+https://github.com/druzsan/justetf-scraping.git'`"
    )
    st.stop()

# Aggiungi la colonna indice (estratto dal nome)
etfs = je.add_index_column(etfs_raw)
st.success(f"Caricati {len(etfs)} ETF con 42 colonne di dati")

# --------------------------------------------------------------------------- #
# Mostra TUTTE le colonne
# --------------------------------------------------------------------------- #
# Riordina: index all'inizio, poi tutte le altre
all_cols = ["index"] + [c for c in etfs.columns if c != "index"]
table = etfs[all_cols].reset_index(drop=True)

st.info(f"📊 **Colonne:** {len(table.columns)} | **ETF:** {len(table)}")

# Mostra in formato compatto (scrollabile)
st.dataframe(table, width="stretch", use_container_width=True, height=500)

# --------------------------------------------------------------------------- #
# Colonne disponibili (per info)
# --------------------------------------------------------------------------- #
with st.expander("📋 Legenda colonne"):
    st.markdown("""
**Identificatori:**
- `index` — indice di riferimento (estratto dal nome dell'ETF)
- `name` — nome completo dell'ETF
- `wkn`, `ticker`, `valor`, `isin` — codici di identificazione

**Info generali:**
- `inception_date`, `age_in_days`, `age_in_years` — data e anzianità
- `strategy` — Long-only, Short, Leveraged
- `domicile_country` — paese di domicilio
- `currency` — valuta (USD, EUR, GBP, ecc.)
- `hedged` — se protetta da cambio
- `securities_lending` — se fa prestito titoli
- `dividends` — Accumulating o Distributing
- `ter` — commissione annuale (%)
- `replication` — Full o Sampling
- `size` — AUM in milioni
- `is_sustainable` — se è ESG
- `number_of_holdings` — numero di titoli in portafoglio

**Rendimenti (ultimi periodi):**
- `yesterday`, `last_week`, `last_month`, `last_three_months`, `last_six_months`
- `last_year`, `last_three_years`, `last_five_years`
- `2025`, `2024`, `2023`, `2022` — rendimento anno per anno

**Volatilità:**
- `last_year_volatility`, `last_three_years_volatility`, `last_five_years_volatility`

**Risk-adjusted returns:**
- `last_year_return_per_risk`, `last_three_years_return_per_risk`, `last_five_years_return_per_risk`

**Drawdown (perdite massime):**
- `max_drawdown`, `last_year_max_drawdown`, `last_three_years_max_drawdown`, `last_five_years_max_drawdown`

**Dividendi:**
- `last_dividends`, `last_year_dividends` — ultimi dividendi staccati
    """)

# --------------------------------------------------------------------------- #
# Download CSV
# --------------------------------------------------------------------------- #
st.divider()
csv_export = je.prepare_export(etfs).to_csv(index=False)

st.download_button(
    label="💾 Scarica CSV (tutte le colonne)",
    data=csv_export.encode("utf-8"),
    file_name="justetf_catalog.csv",
    mime="text/csv",
    use_container_width=True,
)
