import yfinance as yf
import pandas as pd

assets = {
    "S&P 500": "ESE.PA",
    "NASDAQ": "PANX.PA",
    "BTC": "BTC-EUR",
    "ETC Gold (amundi)": "GOLD.MI",
    "ETF Health world": "HLTW.MI",
    "CHF": "CHFEUR=X"
}

tickers = list(set(assets.values()))

def fetch_last_prices(tickers: list[str]) -> dict[str, float]:
    data = yf.download(
        tickers,
        period="1d",
        group_by="ticker"
    )

    prices = {}

    for t in tickers:
        series = data[(t, "Close")].dropna()
        prices[t] = float(series.iloc[-1])
    return prices


csv_path = "/Users/jeandethy/Drive (jeandethy@gmail.com)/Investissement/Suivi_Python/Transactions.csv"

col_asset = "Actif"
col_op  = "Opération"
col_qty   = "Quantité"
col_px = "Prix"
col_fees  = "Frais"

df = pd.read_csv(csv_path, sep=";")
buys = df[df[col_op].str.contains("Achat")].copy()
sells = df[df[col_op].str.contains("Vente")].copy()
print(buys)