from pathlib import Path
import pandas as pd

file = Path("data/processed/APID_2_clean.csv")
df = pd.read_csv(file, low_memory=False)

print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")

summary = pd.DataFrame({
    "signal": df.columns,
    "dtype": df.dtypes.astype(str).values,
    "missing_percent": [
        round(df[col].isna().mean() * 100, 2)
        for col in df.columns
    ],
})

print(summary.to_string(index=False))