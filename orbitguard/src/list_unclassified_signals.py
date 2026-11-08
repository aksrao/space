from pathlib import Path
import pandas as pd

catalog = pd.read_csv("data/processed/signal_catalog.csv")

unclassified = catalog[catalog["subsystem"] == "Review"]

for apid, group in unclassified.groupby("apid"):
    print(f"\n--- {apid}: {len(group)} unclassified signals ---")
    for signal in group["signal"]:
        print(f"- {signal}")