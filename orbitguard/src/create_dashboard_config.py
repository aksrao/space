from pathlib import Path
import pandas as pd

CATALOG = Path("data/processed/signal_catalog.csv")
OUTPUT = Path("config/dashboard_signals.csv")

catalog = pd.read_csv(CATALOG)

# Candidate signal-name patterns for the first dashboard version.
# These are exploratory selections, not validated safety indicators.
rules = [
    ("Power", "power"),
    ("Thermal", "thermal"),
    ("Attitude", "attitude"),
    ("Sensors", "sensor"),
    ("Communications", "communication"),
    ("Housekeeping", "housekeeping"),
]

selected = []

for _, row in catalog.iterrows():
    signal = str(row["signal"])
    apid = str(row["apid"])
    subsystem = str(row["subsystem"])
    name = signal.lower()

    plot_type = None
    dashboard_section = None

    # Power: continuous electrical measurements
    if subsystem == "Power / Electrical" and any(
        term in name for term in [
            "battery", "solar", "3v3", "5v", "charger", "voltage"
        ]
    ):
        dashboard_section = "Power"
        plot_type = "timeseries"

    # Thermal measurements
    elif subsystem == "Thermal" and ("°c" in name or "temp" in name):
        dashboard_section = "Thermal"
        plot_type = "timeseries"

    # Attitude control
    elif subsystem == "ADCS / Actuators" and any(
        term in name for term in ["wheel speed", "wheel accelaration"]
    ):
        dashboard_section = "Attitude"
        plot_type = "timeseries"

    # Sensor measurements
    elif subsystem == "ADCS / Sensors" and any(
        term in name for term in ["gyro", "mag", "sun vector"]
    ):
        dashboard_section = "Sensors"
        plot_type = "timeseries"

    # Communications measurements
    elif subsystem == "Communications" and any(
        term in name for term in ["signal strength", "quality", "baudrate"]
    ):
        dashboard_section = "Communications"
        plot_type = "timeseries"

    # Discrete mode/status fields
    elif subsystem in ["Mode / Configuration", "Status / Configuration"]:
        dashboard_section = "Housekeeping"
        plot_type = "state"

    if dashboard_section:
        selected.append({
            "apid": apid,
            "source_file": row["source_file"],
            "signal": signal,
            "subsystem": subsystem,
            "dashboard_section": dashboard_section,
            "plot_type": plot_type,
            "documentation_verified": False,
        })

config = pd.DataFrame(selected)

if config.empty:
    raise RuntimeError("No candidate signals matched. Check catalog column names.")

config = config.drop_duplicates(
    subset=["source_file", "signal"]
).sort_values(["dashboard_section", "apid", "signal"])

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
config.to_csv(OUTPUT, index=False)

print(f"Saved {len(config)} candidate signals to {OUTPUT}")
print("\nCandidates by dashboard section:")
print(config.groupby("dashboard_section").size().to_string())

print("\nReview the selected signals:")
print(config[["apid", "dashboard_section", "signal"]].to_string(index=False))