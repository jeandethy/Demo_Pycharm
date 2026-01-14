import pandas as pd
import yfinance as yf
import sqlite3
from datetime import date
import streamlit as st

csv_path = "/Users/jeandethy/Drive (jeandethy@gmail.com)/Investissement/Suivi_Python/Transactions.csv"
db_path = "/Users/jeandethy/Drive (jeandethy@gmail.com)/Investissement/Suivi_Python/portfolio.db"

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


def load_and_clean_transactions():
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
    return buys

def compute_summary(buys: pd.DataFrame) -> pd.DataFrame:
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
    summary["current_value"] = summary["quantity"] * summary["last_price"]
    summary["pnl_latente"] = summary["current_value"] - summary["total_cost"]
    summary["pnl_latente_pct"] = (summary["pnl_latente"] / summary["total_cost"]) * 100

    # ajout date snapshot
    summary = summary.reset_index()  # ticker devient une colonne
    summary["asof_date"] = date.today().isoformat()

    return summary

def write_to_sqlite(buys: pd.DataFrame, summary: pd.DataFrame) -> None:
    with sqlite3.connect(db_path) as conn:
        # stocker les transactions (achats) — simple: on remplace à chaque run
        buys.to_sql("transactions_buy", conn, if_exists="replace", index=False)

        # stocker un snapshot du portefeuille (historisé), on garde l'historique en append (une ligne par ticker par date)
        conn.execute("""CREATE TABLE IF NOT EXISTS portfolio_snapshot (asof_date TEXT, ticker TEXT, asset TEXT, quantity REAL, total_cost REAL, fees REAL,
            pru REAL,last_price REAL,current_value REAL,pnl_latente REAL,pnl_latente_pct REAL)
        """)

        summary.to_sql("portfolio_snapshot", conn, if_exists="append", index=False)

def main():
    buys = load_and_clean_transactions()
    summary = compute_summary(buys)
    write_to_sqlite(buys, summary)

    print("\nSnapshot écrit dans SQLite:", db_path)
    print(summary.sort_values("current_value", ascending=False).to_string(index=False))

if __name__ == "__main__":
    main()



st.set_page_config(page_title="Portfolio Dashboard", layout="wide")
st.title("Portfolio Dashboard (test)")

@st.cache_data
def load_latest_snapshot():
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query("SELECT * FROM portfolio_snapshot", conn)

    if df.empty:
        return df, None

    # dernier asof_date
    last_date = df["asof_date"].max()
    latest = df[df["asof_date"] == last_date].copy()
    return latest, last_date


latest, last_date = load_latest_snapshot()

if latest is None or latest.empty:
    st.warning("Aucun snapshot trouvé. Lance d'abord: python update_db.py")
    st.stop()

# KPIs totaux
total_cost = latest["total_cost"].sum()
current_value = latest["current_value"].sum()
pnl = latest["pnl_latente"].sum()
pnl_pct = (pnl / total_cost) * 100 if total_cost else 0.0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Date", last_date)
c2.metric("Valeur totale d'achat", f"{total_cost:,.2f}")
c3.metric("Valeur actuelle", f"{current_value:,.2f}")
c4.metric("PV latente", f"{pnl:,.2f}", f"{pnl_pct:,.2f}%")

st.divider()

# Tableau
st.subheader("Détail par actif")
latest_display = latest.copy()
latest_display["weight"] = latest_display["current_value"] / current_value * 100
latest_display = latest_display.sort_values("current_value", ascending=False)

st.dataframe(
    latest_display[[
        "asset","ticker","quantity","pru","last_price","total_cost",
        "current_value","pnl_latente","pnl_latente_pct","weight"
    ]],
    use_container_width=True
)

st.divider()

# Charts simples
st.subheader("Allocation (valeur actuelle)")
alloc = latest_display.set_index("asset")["current_value"]
st.bar_chart(alloc)

st.subheader("P&L latente par actif")
pnl_by_asset = latest_display.set_index("asset")["pnl_latente"]
st.bar_chart(pnl_by_asset)