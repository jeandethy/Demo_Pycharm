import xlwings as xw
import yfinance as yf
import pandas as pd

def get_data():
    wb = xw.Book("/Users/jeandethy/Drive (jeandethy@gmail.com)/Investissement/Suivi_Python/PBCS_Python.xlsx")
    transactions_sheet = wb.sheets["Transactions"]
    tbl = transactions_sheet.tables["TransactionsTable"]
    df = tbl.range.options(pd.DataFrame, header=1, index=False).value
    df = df.dropna()
    return df

df = get_data()

df['Cout total'] = df['Quantité']*df['Prix']+df['Frais']
print(df)