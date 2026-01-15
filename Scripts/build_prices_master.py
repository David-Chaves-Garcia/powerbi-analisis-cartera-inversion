import yfinance as yf
import pandas as pd

# =====================================================
# CONFIGURACIÓN
# =====================================================

START_DATE = "2020-01-01"
END_DATE = None  # None = hasta hoy

ASSETS_FILE = "assets.csv"
OUTPUT_FILE = "Prices_Master.csv"

# =====================================================
# CARGA DE ACTIVOS (DINÁMICO)
# =====================================================

assets = pd.read_csv(ASSETS_FILE, sep=";")

required_cols = {"Ticker", "Source"}
if not required_cols.issubset(assets.columns):
    raise ValueError("assets.csv debe contener las columnas: Ticker, Source")

# Limpieza defensiva
assets["Ticker"] = assets["Ticker"].str.strip().str.upper()
assets["Source"] = assets["Source"].str.strip()

# =====================================================
# DESCARGA DE PRECIOS
# =====================================================

all_prices = []

for _, row in assets.iterrows():
    ticker_name = row["Ticker"]
    yf_symbol = row["Source"]

    print(f"Descargando {ticker_name} ({yf_symbol})...")

    df = yf.download(
        yf_symbol,
        start=START_DATE,
        end=END_DATE,
        progress=False
    )

    if df.empty:
        print(f"⚠️  Sin datos para {ticker_name}")
        continue

    # Precio ajustado si existe
    price_series = df["Adj Close"] if "Adj Close" in df.columns else df["Close"]

    temp = price_series.reset_index()
    temp.columns = ["Date", "Price"]
    temp["Ticker"] = ticker_name

    all_prices.append(temp)

# =====================================================
# UNIFICAR TODO
# =====================================================

if not all_prices:
    raise RuntimeError("No se ha descargado ningún activo. Revisa assets.csv.")

prices_master = pd.concat(all_prices, ignore_index=True)
prices_master = prices_master.sort_values(["Ticker", "Date"])

# Redondeo a 2 decimales (decisión de diseño)
prices_master["Price"] = prices_master["Price"].round(2)

# =====================================================
# EXPORTAR
# =====================================================

prices_master.to_csv(
    OUTPUT_FILE,
    index=False,
    sep=";",
    decimal=",",
    date_format="%d/%m/%Y"
)

print("✔ Prices_Master.csv generado correctamente")
