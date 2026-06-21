# 📊 JustETF Catalog

App **Streamlit** che scarica il catalogo ETF completo da **JustETF.com** (4.364+ ETF, 42 colonne), estrae l'indice di riferimento dal nome di ogni ETF, e permette di esportare come CSV.

## Cosa fa

1. **Scrapa il catalogo ETF da JustETF.com** — 4.364+ ETF europei con 42 colonne di dati usando [druzsan/justetf-scraping](https://github.com/druzsan/justetf-scraping).

2. **Estrae l'indice di riferimento dal NOME** — non da una descrizione.
   - Esempio: `"iShares Core S&P 500 UCITS ETF USD (Acc)"` → `index = "S&P 500"`
   - Pattern: MSCI (tutte le varianti), S&P, FTSE, Russell, Nikkei, DAX, CAC, IBEX, ecc.
   - Se non trova pattern → `"N/A"`

3. **Mostra tabella completa** — tutte le 42 colonne del catalogo JustETF.

4. **Scarica CSV** — esporta il catalogo con `index` come prima colonna.

## Le 42 colonne

**Identificatori:** `index` | `name` | `wkn` | `ticker` | `valor` | `isin`

**Info generali:** `inception_date` | `age_in_days` | `age_in_years` | `strategy` | `domicile_country` | `currency` | `hedged` | `securities_lending` | `dividends` | `ter` | `replication` | `size` | `is_sustainable` | `number_of_holdings`

**Rendimenti (%):** `yesterday` | `last_week` | `last_month` | `last_three_months` | `last_six_months` | `last_year` | `last_three_years` | `last_five_years` | `2025` | `2024` | `2023` | `2022`

**Volatilità & Risk (%):** `last_year_volatility` | `last_three_years_volatility` | `last_five_years_volatility` | `last_year_max_drawdown` | `last_three_years_max_drawdown` | `last_five_years_max_drawdown` | `max_drawdown`

**Return per Risk:** `last_year_return_per_risk` | `last_three_years_return_per_risk` | `last_five_years_return_per_risk`

**Dividendi:** `last_dividends` | `last_year_dividends`

## Logica di estrazione dell'indice

```python
# Pattern cercati nel campo NAME dell'ETF (in ordine di specificità):
1. MSCI (ACWI, World, USA, China, EM, Europe, Japan, ecc.)
2. S&P (500, 1000, 600, ecc.)
3. FTSE (100, 250, All-World, ecc.)
4. Russell (2000, 1000, ecc.)
5. Nikkei 225
6. DAX, CAC 40, IBEX 35, AEX, STOXX
```

Se il nome contiene uno di questi pattern, lo estrae; altrimenti ritorna `"N/A"`.

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
- **Primo caricamento**: ~1-2 minuti (dipende dalla rete). Poi cachato per 1 ora.
- **CSV completo**: il download contiene tutte le 42 colonne, con `index` come prima colonna.

## Struttura

| File | Ruolo |
|------|-------|
| `justetf.py` | Scraping JustETF + estrazione indice dal nome |
| `app.py` | Interfaccia Streamlit |
| `requirements.txt` | Dipendenze |
| `start.bat` | Launcher Windows |
| `.devcontainer/` | Config per Codespaces / Streamlit Cloud |

## Crediti

- **JustETF.com** — catalogo ETF europei
- [druzsan/justetf-scraping](https://github.com/druzsan/justetf-scraping) — libreria scraping

**Disclaimer**: app a scopo didattico/personale.
