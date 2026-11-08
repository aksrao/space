from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/processed")
OUTPUT_FILE = DATA_DIR / "signal_inventory.csv"

records = []

for file in sorted(DATA_DIR.glob("*_clean.csv")):
    print(f"Profiling {file.name}")
    df = pd.read_csv(file, low_memory=False)

    timestamp_col = "RecordingTime"
    if timestamp_col in df.columns:
        df[timestamp_col] = pd.to_datetime(
            df[timestamp_col],
            errors="coerce"
        )

    for column in df.columns:
        if column == timestamp_col:
            continue

        values = pd.to_numeric(df[column], errors="coerce")
        valid_count = int(values.notna().sum())

        # Include columns with at least one numeric value.
        if valid_count == 0:
            continue

        records.append({
            "source_file": file.name,
            "signal": column,
            "numeric_dtype": str(values.dtype),
            "rows": len(df),
            "valid_values": valid_count,
            "missing_values": int(values.isna().sum()),
            "missing_percent": round(values.isna().mean() * 100, 2),
            "minimum": values.min(),
            "median": values.median(),
            "maximum": values.max(),
            "unique_values": int(values.nunique()),
        })

inventory = pd.DataFrame(records)

inventory = inventory.sort_values(
    ["source_file", "missing_percent", "signal"]
)

inventory.to_csv(OUTPUT_FILE, index=False)

print(f"\nSaved signal inventory: {OUTPUT_FILE}")
print(f"Numeric signals profiled: {len(inventory)}")

print("\nMost complete signals:")
print(
    inventory.sort_values("missing_percent")
    [["source_file", "signal", "missing_percent", "minimum", "median", "maximum"]]
    .head(30)
    .to_string(index=False)
)

print("\nSignals with more than 10% missing data:")
print(
    inventory[inventory["missing_percent"] > 10]
    [["source_file", "signal", "missing_percent"]]
    .to_string(index=False)
)