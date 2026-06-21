# 📊 JustETF Catalog

App **Streamlit** semplice che scarica il catalogo ETF da **JustETF.com**, estrae l'indice di riferimento dalla descrizione, e permette di esportare come CSV.

## Cosa fa

1. **Scrapa il catalogo ETF da JustETF.com** — usando la libreria [druzsan/justetf-scraping](https://github.com/druzsan/justetf-scraping).
2. **Estrae l'indice di riferimento** — dalla descrizione di ogni ETF (MSCI WORLD, S&P 500, FTSE, Russell, ecc.).
3. **Filtra per TER** — scegli il massimo commissione annuale.
4. **Mostra una tabella** — con nome, ISIN, TER, indice di riferimento.
5. **Scarica CSV** — esporta la lista filtrata come file CSV.

## Avvio locale

```bash
pip install -r requirements.txt
streamlit run app.py
```

Oppure doppio clic su `start.bat` (Windows).

## Deploy su Streamlit Cloud

1. Accedi a [share.streamlit.io](https://share.streamlit.io) con GitHub.
2. "Create app" → Repository: `madidos/justetf-index`, Branch: `main`, Main file: `app.py`.
3. Deploy (1-2 min).

### Note
- **Primo caricamento lento**: il primo accesso scarica il catalogo completo da JustETF (qualche minuto). Poi viene cachato per 1 ora.
- **Estrazione indice**: usa pattern regex per cercare MSCI, S&P, FTSE, Russell, ecc. nella descrizione. Se non trova niente, ritorna "N/A".
- **CSV ordinato**: il download CSV è ordinato per TER crescente (commissioni piu basse in alto).

## Struttura

| File | Ruolo |
|------|-------|
| `justetf.py` | Scraping e estrazione indice dalla descrizione |
| `app.py` | Interfaccia Streamlit (carica, filtra, scarica CSV) |
| `requirements.txt` | Dipendenze (streamlit, pandas, justetf-scraping) |
| `start.bat` | Launcher Windows |
| `.devcontainer/` | Config per GitHub Codespaces / Streamlit Cloud |

## Crediti

- **JustETF.com** — catalogo ETF europei
- [druzsan/justetf-scraping](https://github.com/druzsan/justetf-scraping) — libreria scraping

**Disclaimer**: app a scopo didattico/personale. Nessuna garanzia sui dati.
