import pandas as pd

# =====================================================
# CONFIGURACIÓN
# =====================================================

INPUT_FILE = "Prices_Master.csv"
OUTPUT_FILE = "Prices_Filled.csv"

DATE_FORMAT = "%d/%m/%Y"

# =====================================================
# CARGA DE PRECIOS RAW
# =====================================================

prices = pd.read_csv(
    INPUT_FILE,
    sep=";",
    decimal=",",
    parse_dates=["Date"],
    dayfirst=True
)

prices = prices.sort_values(["Ticker", "Date"])

# =====================================================
# RANGO GLOBAL DE FECHAS
# =====================================================

global_start = prices["Date"].min()
global_end = prices["Date"].max()

all_dates = pd.date_range(
    start=global_start,
    end=global_end,
    freq="D"
)

# =====================================================
# FILL-FORWARD POR ACTIVO
# =====================================================

filled_frames = []

for ticker, group in prices.groupby("Ticker"):
    group = group.set_index("Date").sort_index()

    # Reindex diario
    group = group.reindex(all_dates)

    # Fill-forward SOLO después del primer dato válido
    group["Price"] = group["Price"].ffill()

    # Restaurar columnas
    group["Ticker"] = ticker
    group = group.reset_index().rename(columns={"index": "Date"})

    filled_frames.append(group)

# =====================================================
# UNIFICAR TODO
# =====================================================

prices_filled = pd.concat(filled_frames, ignore_index=True)
prices_filled = prices_filled.sort_values(["Ticker", "Date"])

# 🔧 Redondeo final
prices_filled["Price"] = prices_filled["Price"].round(2)

# =====================================================
# EXPORTAR
# =====================================================

prices_filled.to_csv(
    OUTPUT_FILE,
    index=False,
    sep=";",
    decimal=",",
    date_format=DATE_FORMAT
)

print("✔ Prices_Filled.csv generado correctamente")
