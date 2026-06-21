# 📊 JustETF Index

App **Streamlit** che scrapa gli ETF europei da **JustETF.com**, scarica le loro quotazioni reali (Yahoo Finance), e valuta **portafogli equally weighted** come combinazioni di ETF selezionati.

## Cosa fa

1. **Scrapa il catalogo ETF da JustETF** — accede a [JustETF.com](https://justetf.com) (il piu grande repository europeo di dati sugli ETF) usando la libreria [druzsan/justetf-scraping](https://github.com/druzsan/justetf-scraping).

2. **Filtra gli ETF** — per TER massima e regione/asset class.

3. **Scarica le quotazioni reali** — daily closing price di ogni ETF da Yahoo Finance, le converte a serie mensile.

4. **Valuta tutte le combinazioni EW** — come in [equally-weighted-index](https://github.com/madidos/equally-weighted-index), ma su ETF reali. Calcola rendimento annualizzato, volatilita e Sharpe-like per ogni combo.

5. **Confronta col benchmark** — scegli un ETF (es. VWCE.DE = FTSE All-World) e visualizza il valore cumulato + rendimento rolling del tuo portafoglio vs il benchmark.

## Metodologia

**Equally weighted, non ribilanciato**: ogni ETF entra con lo stesso capitale, nessun ribilanciamento.

```
montante_t = media_etf( P_t / P_{t-months} )
rendimento_ann = media(montante) ** (12/months) − 1
volatilita = std(montante)
```

## Avvio locale

```bash
pip install -r requirements.txt
streamlit run app.py
```

Oppure doppio clic su `start.bat` (Windows).

## Deploy su Streamlit Cloud

1. Repo pubblico su GitHub: ✓
2. Accedi a [share.streamlit.io](https://share.streamlit.io) con GitHub.
3. "Create app" → Repository: `madidos/justetf-index`, Branch: `main`, Main file: `app.py`.
4. Deploy (1-3 min).

### Note
- Il primo caricamento degli ETF da JustETF puo richiedere qualche minuto (dipende dalla rete). Poi vengono cachati per un'ora.
- Il mapping ISIN → ticker Yahoo Finance è semplificato; in produzione usaremmo una lookup table esterna.
- L'app scarica dati "grezzi" da yfinance (senza aggiustamenti per dividendi/split); per un'analisi rigorosa serve total-return adjustment.

## Struttura

| File | Ruolo |
|------|-------|
| `justetf.py` | Scraping e processing del catalogo ETF da JustETF.com |
| `etf_analysis.py` | Logica EW: download yfinance, statistiche, combinazioni |
| `app.py` | Interfaccia Streamlit |
| `requirements.txt` | Dipendenze (streamlit, pandas, yfinance, justetf-scraping) |
| `start.bat` | Launcher Windows |
| `.devcontainer/` | Config per GitHub Codespaces / Streamlit Cloud |

## Crediti & legale

- **JustETF.com** — catalogo ETF europei
- **Yahoo Finance** — quotazioni storiche
- [druzsan/justetf-scraping](https://github.com/druzsan/justetf-scraping) — libreria scraping

**Disclaimer**: app a scopo didattico/personale. Nessuna garanzia sui dati. Non è consulenza finanziaria.
