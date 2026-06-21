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
    "con l'indice di riferimento estratto dalla descrizione. Esporta in CSV."
)

# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("⚙️ Impostazioni")
    ter_max = st.slider("TER massima (%)", 0.0, 2.0, 0.5, step=0.05,
                        help="Filtra gli ETF per commissione annuale massima.")
    st.divider()
    st.caption("Dati: JustETF.com")


@st.cache_data(show_spinner=False, ttl=3600)
def cached_justetf_overview():
    return je.load_justetf_overview()


# --------------------------------------------------------------------------- #
# 1) Caricamento ETF da JustETF
# --------------------------------------------------------------------------- #
st.subheader("1 · Scarica il catalogo ETF")

if st.button("▶️ Avvia il download da JustETF.com", type="primary"):
    with st.spinner("Scarico il catalogo da JustETF.com… (questo puo richiedere un minuto)"):
        etfs_raw = cached_justetf_overview()
    st.session_state.etfs_raw = etfs_raw
else:
    etfs_raw = st.session_state.get("etfs_raw")

if etfs_raw is None:
    st.info("Clicca il bottone **Avvia** per scaricare il catalogo degli ETF da JustETF.com")
    st.stop()

if etfs_raw.empty:
    st.error(
        "❌ Impossibile scaricare il catalogo da JustETF. "
        "Verifica che `justetf-scraping` sia installato.\n\n"
        "Installa con:\n"
        "`pip install 'justetf-scraping @ git+https://github.com/druzsan/justetf-scraping.git'`"
    )
    st.stop()

# Aggiungi la colonna indice
etfs = je.add_index_column(etfs_raw)
st.success(f"✓ Caricati {len(etfs)} ETF.")

# --------------------------------------------------------------------------- #
# 2) Filtraggio
# --------------------------------------------------------------------------- #
st.subheader("2 · Filtra e visualizza")

if "ter" in etfs.columns:
    etfs_filtered = etfs[etfs["ter"] <= ter_max / 100].copy()
    st.caption(f"ETF con TER ≤ {ter_max}%: **{len(etfs_filtered)}**")
else:
    etfs_filtered = etfs.copy()
    st.warning("Colonna 'ter' non trovata nel catalogo.")

# --------------------------------------------------------------------------- #
# 3) Mostra tabella con colonne principali
# --------------------------------------------------------------------------- #
st.subheader("3 · Tabella")

# Prepara le colonne da mostrare
display_cols = []
for col in ["name", "isin", "ter", "index"]:
    if col in etfs_filtered.columns:
        display_cols.append(col)

if not display_cols:
    st.error("Nessuna colonna disponibile per la visualizzazione.")
    st.stop()

table = etfs_filtered[display_cols].reset_index(drop=True)
st.dataframe(table, width="stretch", use_container_width=True)

st.caption(f"Totale righe: {len(table)}")

# --------------------------------------------------------------------------- #
# 4) Download CSV
# --------------------------------------------------------------------------- #
st.subheader("4 · Scarica CSV")

csv_export = je.prepare_export(etfs_filtered).to_csv(index=False)

st.download_button(
    label="💾 Scarica CSV",
    data=csv_export.encode("utf-8"),
    file_name="justetf_catalog.csv",
    mime="text/csv",
    help="Scarica la tabella filtrata come file CSV.",
)
