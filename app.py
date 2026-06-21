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

# Aggiungi la colonna indice
etfs = je.add_index_column(etfs_raw)
st.success(f"✓ Caricati {len(etfs)} ETF")

# --------------------------------------------------------------------------- #
# Mostra tabella completa
# --------------------------------------------------------------------------- #
# Riordina le colonne con index all'inizio
cols_order = ["index", "name", "isin", "ter"]
display_cols = [col for col in cols_order if col in etfs.columns]

if not display_cols:
    st.error("Nessuna colonna disponibile.")
    st.stop()

table = etfs[display_cols].reset_index(drop=True)
st.dataframe(table, width="stretch", use_container_width=True, height=400)

st.caption(f"**Totale ETF:** {len(table)}")

# --------------------------------------------------------------------------- #
# Download CSV
# --------------------------------------------------------------------------- #
csv_export = je.prepare_export(etfs).to_csv(index=False)

st.download_button(
    label="💾 Scarica CSV",
    data=csv_export.encode("utf-8"),
    file_name="justetf_catalog.csv",
    mime="text/csv",
    use_container_width=True,
)
