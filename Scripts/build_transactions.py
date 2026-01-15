# =====================================================
# SIMULACIÓN DE TRANSACCIONES PARA CARTERA DE INVERSIÓN
# (VERSIÓN BASE – SIN BUY & HOLD, CON LÍMITE DE CAPITAL)
# =====================================================

import pandas as pd
import random
import uuid

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================

FEE_RATE = 0.005  # 0.5 %

MAX_MONTHLY_INVESTMENT = 300  # € máximo a invertir al mes

# Activos con DCA mensual
DCA_ASSETS = {
    "BTC": 50,
    "URTH": 50,
    "EEM": 25
}

# Operativa manual GLOBAL por mes
MIN_BUYS_PER_MONTH = 1
MAX_BUYS_PER_MONTH = 5
MIN_SELLS_PER_MONTH = 0
MAX_SELLS_PER_MONTH = 2

# Tamaño económico por operación (USD)
MIN_MANUAL_BUY_USD = 20
MAX_MANUAL_BUY_USD = 100
MIN_MANUAL_SELL_USD = 10
MAX_MANUAL_SELL_USD = 50

# =====================================================
# CARGA DE ACTIVOS (FUENTE ÚNICA)
# =====================================================

assets = pd.read_csv("assets.csv", sep=";")
assets["Ticker"] = assets["Ticker"].str.strip().str.upper()
ALL_ASSETS = assets["Ticker"].tolist()

# =====================================================
# LECTURA DE PRECIOS (FUENTE DEFINITIVA)
# =====================================================

prices = pd.read_csv(
    "Prices_Filled.csv",
    sep=";",
    decimal=",",
    parse_dates=["Date"],
    dayfirst=True
)

prices = prices.sort_values(["Ticker", "Date"])
prices["Month"] = prices["Date"].dt.to_period("M")

# =====================================================
# VALIDACIONES
# =====================================================

missing_dca = set(DCA_ASSETS.keys()) - set(ALL_ASSETS)
if missing_dca:
    raise ValueError(f"Activos DCA no presentes en assets.csv: {missing_dca}")

# =====================================================
# FUNCIÓN PARA CREAR TRANSACCIONES
# =====================================================

def create_transaction(date, ticker, quantity, price, strategy):
    gross = price * quantity
    fees = abs(gross) * FEE_RATE
    net = gross - fees

    return {
        "TransactionID": str(uuid.uuid4()),
        "Date": date,
        "Ticker": ticker,
        "Quantity": round(quantity, 6),
        "Price": round(price, 2),
        "GrossAmount": round(gross, 2),
        "Fees": round(fees, 2),
        "NetAmount": round(net, 2),
        "AbsoluteAmount": round(abs(gross), 2),
        "FeePct": FEE_RATE,
        "TransactionType": "Buy" if quantity > 0 else "Sell",
        "Strategy": strategy
    }

# =====================================================
# GENERACIÓN DE TRANSACCIONES
# =====================================================

transactions = []
positions = {ticker: 0 for ticker in ALL_ASSETS}

# -----------------------------
# DCA MENSUAL (RESPETA EL LÍMITE)
# -----------------------------

monthly_invested = {}

for ticker, monthly_cash in DCA_ASSETS.items():
    df = prices[prices["Ticker"] == ticker]
    monthly_prices = df.groupby("Month").first().reset_index()

    for _, row in monthly_prices.iterrows():
        month = row["Month"]
        date = row["Date"]
        price = row["Price"]

        invested = monthly_invested.get(month, 0)
        remaining = MAX_MONTHLY_INVESTMENT - invested

        if remaining <= 0:
            continue

        cash = min(monthly_cash, remaining)
        quantity = cash / price

        transactions.append(
            create_transaction(date, ticker, quantity, price, "DCA")
        )

        positions[ticker] += quantity
        monthly_invested[month] = invested + cash

# -----------------------------
# OPERATIVA MANUAL (RESPETA EL LÍMITE)
# -----------------------------

for month, group in prices.groupby("Month"):

    invested = monthly_invested.get(month, 0)
    remaining = MAX_MONTHLY_INVESTMENT - invested

    n_buys = random.randint(MIN_BUYS_PER_MONTH, MAX_BUYS_PER_MONTH)
    n_sells = random.randint(MIN_SELLS_PER_MONTH, MAX_SELLS_PER_MONTH)

    # COMPRAS MANUALES
    for _ in range(n_buys):
        if remaining <= 0:
            break

        ticker = random.choice(ALL_ASSETS)
        df_ticker = group[group["Ticker"] == ticker]

        if df_ticker.empty:
            continue

        row = df_ticker.sample(1).iloc[0]
        date = row["Date"]
        price = row["Price"]

        cash = random.uniform(MIN_MANUAL_BUY_USD, MAX_MANUAL_BUY_USD)
        cash = min(cash, remaining)

        if cash <= 0:
            continue

        quantity = cash / price

        transactions.append(
            create_transaction(date, ticker, quantity, price, "Manual")
        )

        positions[ticker] += quantity
        invested += cash
        remaining -= cash
        monthly_invested[month] = invested

    # VENTAS MANUALES (NO AFECTAN AL LÍMITE)
    for _ in range(n_sells):
        ticker = random.choice(ALL_ASSETS)

        if positions[ticker] <= 0:
            continue

        df_ticker = group[group["Ticker"] == ticker]
        if df_ticker.empty:
            continue

        row = df_ticker.sample(1).iloc[0]
        date = row["Date"]
        price = row["Price"]

        position_value = positions[ticker] * price
        if position_value < MIN_MANUAL_SELL_USD:
            continue

        cash = random.uniform(
            MIN_MANUAL_SELL_USD,
            min(MAX_MANUAL_SELL_USD, position_value)
        )

        quantity = cash / price

        transactions.append(
            create_transaction(date, ticker, -quantity, price, "Manual")
        )

        positions[ticker] -= quantity
        positions[ticker] = max(positions[ticker], 0)

# =====================================================
# EXPORTAR RESULTADO
# =====================================================

transactions_df = pd.DataFrame(transactions)
transactions_df.sort_values("Date", inplace=True)

transactions_df.to_csv(
    "Transactions.csv",
    index=False,
    sep=";",
    decimal=","
)

print("✔ Transactions.csv generado correctamente")
