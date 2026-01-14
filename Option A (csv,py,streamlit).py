import pandas as pd
import yfinance as yf

csv_path = "/Users/jeandethy/Drive (jeandethy@gmail.com)/Investissement/Suivi_Python/Transactions.csv"

col_asset = "Actif"
col_op  = "Opération"
col_qty   = "Quantité"
col_px = "Prix"
col_fees  = "Frais"

assets = {
    "S&P 500": "ESE.PA",
    "NASDAQ": "PANX.PA",
    "BTC": "BTC-EUR",
    "ETC Gold (amundi)": "GOLD.MI",
    "ETF Health world": "HLTW.MI",
    "CHF": "CHFEUR=X"}

tickers = list(set(assets.values()))

def fetch_last_prices(tickers: list[str]) -> dict[str, float]:
    data = yf.download(tickers, period="1d", group_by="ticker")
    prices = {}

    for t in tickers:
        series = data[(t, "Close")].dropna()
        prices[t] = float(series.iloc[-1])
    return prices


def main():
    df = pd.read_csv(csv_path, sep=";")

    buys = df[df[col_op].str.contains("Achat")].copy()
    # sells = df[df[col_op].str.contains("Vente")].copy()

    # On converti en str, supprime les ",", puis transforme en float
    for c in [col_qty, col_px, col_fees]:
        buys[c] = (
            buys[c].astype(str)
            .str.replace(" ", "")
            .str.replace(",", ".")
        )
        buys[c] = pd.to_numeric(buys[c]).fillna(0)
    buys["total_cost"] = buys[col_qty] * buys[col_px] + buys[col_fees]

    # Créer une colonne ticker
    inv_assets = {name: ticker for name, ticker in assets.items()}
    buys["ticker"] = buys[col_asset].map(inv_assets)

    # Prix actuels
    last_prices = fetch_last_prices(tickers)

    # Création de la table summary
    summary = (
        buys.groupby("ticker").agg(
            asset = (col_asset, "first"),
            quantity=(col_qty, "sum"),
            total_cost=("total_cost", "sum"),
            fees=(col_fees, "sum")
        )
    )
    summary["pru"] = summary["total_cost"] / summary["quantity"]
    summary["last_price"] = summary.index.map(last_prices)
    summary["pnl_latente"] = (summary["last_price"]-summary["pru"])*summary["quantity"]
    return summary.round(2)

if __name__ == "__main__":
    main()

summary = main()
print(summary.to_string())