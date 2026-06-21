"""
app.py — Interfaccia web (Streamlit) per analizzare portafogli EW su ETF reali da JustETF.

Avvio:
    pip install -r requirements.txt
    streamlit run app.py

Si apre nel browser su http://localhost:8501
"""

from __future__ import annotations

import logging

import pandas as pd
import streamlit as st

import etf_analysis as ea
import justetf as je

logging.basicConfig(level=logging.INFO)

st.set_page_config(page_title="JustETF Index", page_icon="📊", layout="wide")

st.title("📊 Portafogli equally weighted su ETF da JustETF")
st.caption(
    "Scrapa gli ETF europei da JustETF.com, scarica le quote reali (Yahoo Finance), "
    "valuta tutte le combinazioni equally weighted e le confronta con un benchmark."
)

with st.expander("Come funziona", expanded=False):
    st.markdown(
        """
- **Sorgente ETF**: scraping da JustETF.com (il catalogo piu completo di ETF europei).
- **Quote**: scaricate da Yahoo Finance (giornaliere → convertite a mensili).
- **Analisi**: come in *equally-weighted-index*, ma su ETF veri invece che indici MSCI.
- **Benchmark**: scegli un ETF come benchmark (es. VWCE.DE = FTSE All-World).

> Nota: il primo caricamento degli ETF da JustETF puo richiedere qualche minuto
> (dipende dalla rete). Poi vengono cachati per un'ora.
        """
    )

# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("⚙️ Impostazioni")
    months = st.slider(
        "Orizzonte (mesi)", 12, 240, 120, step=12,
        help="Finestra su cui misurare il montante del portafoglio.",
    )
    benchmark_ticker = st.text_input("Benchmark (ticker Yahoo)", value="VWCE.DE")
    st.divider()
    st.caption("Dati ETF: JustETF + Yahoo Finance.")


@st.cache_data(show_spinner=False, ttl=3600)
def cached_justetf_overview():
    return je.load_justetf_overview()


@st.cache_data(show_spinner=False, ttl=3600)
def cached_download_etf_prices(tickers_tuple: tuple, period: str):
    return ea.download_etf_prices(list(tickers_tuple), period=period)


# --------------------------------------------------------------------------- #
# 1) Caricamento ETF da JustETF
# --------------------------------------------------------------------------- #
st.subheader("1 · Catalogo ETF da JustETF")

with st.spinner("Scarico il catalogo ETF da JustETF.com…"):
    etfs_catalog = cached_justetf_overview()

if etfs_catalog is None or etfs_catalog.empty:
    st.error(
        "Impossibile scaricare il catalogo da JustETF. "
        "Verifica che `justetf-scraping` sia installato."
    )
    st.stop()

st.success(f"Caricati {len(etfs_catalog)} ETF.")
st.dataframe(etfs_catalog.head(10), width="stretch")

# --------------------------------------------------------------------------- #
# 2) Selezione ETF
# --------------------------------------------------------------------------- #
st.subheader("2 · Selezione ETF per l'analisi")

# Filtri
col_ter, col_region = st.columns(2)
with col_ter:
    ter_max = st.slider("TER massima (%)", 0.0, 1.0, 0.5, step=0.05)
with col_region:
    region = st.text_input("Regione (es. 'MSCI WORLD', 'USA')", value="")

# Filtra il catalogo
filtered = je.filter_etfs(etfs_catalog, ter_max=ter_max / 100, region=region if region else None)
st.caption(f"ETF che rispettano i filtri: {len(filtered)}")

# Selezione manuale
selected_isins = st.multiselect(
    "Scegli gli ISIN degli ETF da analizzare",
    options=filtered.get("isin", pd.Series([])).unique() if "isin" in filtered.columns else [],
    max_selections=15,
)

if not selected_isins:
    st.info("Seleziona almeno un ETF per continuare.")
    st.stop()

# Estrai i nomi e i ticker (se disponibili)
selected_etfs = filtered[filtered.get("isin", pd.Series([])).isin(selected_isins)].copy()
if selected_etfs.empty:
    st.error("ETF selezionati non trovati nel catalogo filtrato.")
    st.stop()

st.dataframe(selected_etfs[["isin", "name", "ter"] if "ter" in selected_etfs.columns else ["isin", "name"]], width="stretch")

# Tenta di risolvere i ticker Yahoo Finance
st.caption("Ricerca dei ticker Yahoo Finance… (potrebbe richiedere un minuto)")
with st.spinner("Mapping ISIN → ticker Yahoo…"):
    selected_etfs = je.add_yahoo_tickers(selected_etfs)

valid_tickers = selected_etfs[selected_etfs["yahoo_ticker"].notna()]["yahoo_ticker"].tolist()
if not valid_tickers:
    st.error("Non riesco a mappare nessuno degli ISIN a ticker Yahoo Finance.")
    st.stop()

st.success(f"Trovati {len(valid_tickers)} ticker Yahoo validi.")
st.write("Ticker:", ", ".join(valid_tickers))

# --------------------------------------------------------------------------- #
# 3) Scaricamento prezzi ETF
# --------------------------------------------------------------------------- #
st.subheader("3 · Download prezzi ETF")

if st.button("⬇️ Scarica le quotazioni da Yahoo Finance (ultimi 10 anni)"):
    with st.spinner("Scarico i prezzi…"):
        try:
            prices_daily = cached_download_etf_prices(tuple(valid_tickers), period="10y")
            prices_monthly = ea.resample_to_monthly(prices_daily)
            st.session_state.prices = prices_monthly
            st.session_state.tickers = valid_tickers
            st.success(f"Scaricati {len(prices_monthly)} mesi per {len(valid_tickers)} ETF.")
            st.dataframe(prices_monthly.tail(5), width="stretch")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Errore nel download: {exc}")

if "prices" not in st.session_state:
    st.info("Clicca il bottone per scaricare i prezzi.")
    st.stop()

prices = st.session_state.prices
tickers = st.session_state.tickers

# --------------------------------------------------------------------------- #
# 4) Statistiche
# --------------------------------------------------------------------------- #
st.subheader("4 · Statistiche per ETF")

st.dataframe(ea.summary_stats(prices, window=months), width="stretch")

# --------------------------------------------------------------------------- #
# 5) Combinazioni EW
# --------------------------------------------------------------------------- #
st.subheader("5 · Combinazioni equally weighted")

k = st.slider("Numero di ETF per portafoglio (k)", 1, min(5, len(tickers)), 2)
n_comb = ea.count_combinations(len(tickers), k)
st.caption(f"Combinazioni: {n_comb:,}")

if n_comb > 50_000:
    st.warning(f"{n_comb:,} combinazioni: il calcolo puo richiedere un po'. Riduci k.")

if st.button("▶️ Valuta le combinazioni", type="primary"):
    prog = st.progress(0.0, text="Valuto…")

    def _progress(done: int, total: int) -> None:
        prog.progress(done / total, text=f"{done:,}/{total:,}")

    results = ea.evaluate_combinations(prices, k=k, months=months, progress=_progress)
    prog.empty()
    st.session_state.results = results

    st.success(f"Valutate {len(results)} combinazioni valide.")
    st.dataframe(results.nlargest(10, "sharpe"), width="stretch")

    st.download_button(
        "💾 Scarica risultati (CSV)",
        results.to_csv().encode("utf-8"),
        file_name="etf_combinazioni_ew.csv",
        mime="text/csv",
    )

# --------------------------------------------------------------------------- #
# 6) Confronto vs benchmark
# --------------------------------------------------------------------------- #
if st.session_state.get("results") is not None:
    st.subheader("6 · Confronto col benchmark")

    results = st.session_state.results
    choice = st.radio(
        "Portafoglio da confrontare",
        ["Massimo Sharpe", "Minima volatilita", "Massimo rendimento"],
        horizontal=True,
    )
    if choice == "Massimo Sharpe":
        label = results["sharpe"].idxmax()
    elif choice == "Minima volatilita":
        label = results["vol"].idxmin()
    else:
        label = results["return"].idxmax()

    which = [t.strip() for t in label.split(",")]
    st.caption(f"Portafoglio: {label}")

    if benchmark_ticker and benchmark_ticker not in which:
        # Scarica il benchmark
        try:
            benchmark_prices = cached_download_etf_prices((benchmark_ticker,), period="10y")
            benchmark_monthly = ea.resample_to_monthly(benchmark_prices)
        except Exception:  # noqa: BLE001
            st.error(f"Non riesco a scaricare il benchmark {benchmark_ticker}.")
            benchmark_monthly = None
    else:
        benchmark_monthly = None

    # Valore cumulato
    port_val = ea.equal_weight_value(prices, which)
    if not port_val.empty and benchmark_monthly is not None:
        val_df = pd.DataFrame(
            {"Portafoglio": port_val, benchmark_ticker: benchmark_monthly[benchmark_ticker]}
        ).dropna(how="all")
        if not val_df.empty:
            val_df.index = val_df.index.to_timestamp()
            st.line_chart(val_df, width="stretch")

    # Rendimento rolling
    port_roll = ea.rolling_return(prices, which, months)
    st.caption(f"Rendimento rolling {months} mesi del portafoglio")
    if not port_roll.empty:
        port_roll_df = port_roll.to_frame("Portafoglio")
        port_roll_df.index = port_roll_df.index.to_timestamp()
        st.line_chart(port_roll_df, width="stretch")
        st.dataframe(port_roll_df.describe(), width="stretch")
