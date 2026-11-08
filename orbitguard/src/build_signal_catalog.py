from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/processed")
INVENTORY_FILE = DATA_DIR / "signal_inventory.csv"
OUTPUT_FILE = DATA_DIR / "signal_catalog.csv"

inventory = pd.read_csv(INVENTORY_FILE)

# Keep signals with at least 95% non-missing values.
catalog = inventory[inventory["missing_percent"] <= 5].copy()

def assign_subsystem(signal: str, apid: str) -> str:
    name = signal.lower()
        # Sun sensor channels
    if "sunsensor" in name or "sun sensor" in name:
        return "ADCS / Sensors"

    # Wheel drive electronics and wheel acceleration
    if "wheel drive electronic" in name or "wheel accelaration" in name:
        return "ADCS / Actuators"

    # Spacecraft and subsystem modes
    if any(x in name for x in [
        "beacon mode", "com system mode"
    ]):
        return "Communications"

    if any(x in name for x in [
        "satellite mode", "acs mode"
    ]):
        return "Mode / Configuration"

    # Command handling counters
    if any(x in name for x in [
        "ctr immediate tc", "ctr time tagged tc",
        "ctr change param"
    ]):
        return "OBC / Housekeeping"

    # OBC and TNC discrete status fields
    if "onboard computer" in name:
        return "OBC / Housekeeping"

    if "terminal node controller" in name:
        return "Communications"

    # Thermal measurements
    if any(x in name for x in ["temp", "temperature", "°c"]):
        return "Thermal"

    # Communications
    if any(x in name for x in [
        "trx", "transceiver", "tnc", "baudrate",
        "signal strength", "receiving", "g/s contact",
        "auto send"
    ]):
        return "Communications"

    # OBC, software, storage, command/error counters, and time
    if any(x in name for x in [
        "obc", "boot", "software revision", "command",
        "err ctr", "error", "uptime", "telemetry flash",
        "onboard time", "housekeeping", "active pcu",
        "active obc", "selected can bus", "startup"
    ]):
        return "OBC / Housekeeping"

    # ADCS sensors
    if any(x in name for x in [
        "magnetic field", "mfs", "sun sensor", "sun vector",
        "gyro", "quaternion", "mag_if"
    ]):
        return "ADCS / Sensors"

    # ADCS actuators
    if any(x in name for x in [
        "magnetic coil", "wheel speed", "wheel acceleration",
        "wheelcontroller"
    ]):
        return "ADCS / Actuators"

    # Orbit and navigation
    if any(x in name for x in [
        "position", "velocity", "orbit"
    ]):
        return "Orbit / Navigation"

    # Power measurements and electrical loads
    if any(x in name for x in [
        "battery", "solar", "charger", "voltage", "current",
        "3v3", "5v", "pcu", "pcdu", "power", "bus"
    ]):
        return "Power / Electrical"

    # Discrete status and configuration fields
    if any(x in name for x in [
        "flag", "polarity", "switch", "channel",
        "can bus", "camera", "payload", "antenna",
        "inactive", "free command pool", "id",
        "check channel", "shadow"
    ]):
        return "Status / Configuration"

    return "Review"

catalog["apid"] = catalog["source_file"].str.extract(r"(APID_\d+)")
catalog["subsystem"] = catalog.apply(
    lambda row: assign_subsystem(row["signal"], row["apid"]),
    axis=1
)
catalog["dashboard_priority"] = catalog["subsystem"].map({
    "Power": "High",
    "Thermal": "High",
    "Attitude / Sensors": "Medium",
    "Housekeeping": "Medium",
    "Orbit": "Low",
    "Unclassified": "Review",
})

catalog.to_csv(OUTPUT_FILE, index=False)

print(f"Saved catalog: {OUTPUT_FILE}")
print("\nSignals by APID and subsystem:")
print(
    catalog.groupby(["apid", "subsystem"])
    .size()
    .to_string()
)