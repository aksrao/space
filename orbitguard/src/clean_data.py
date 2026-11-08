from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/b2")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

APID_FILES = [
    "APID_1.csv",
    "APID_4.csv",
    "APID_40.csv",
    "APID_41.csv",
]

TIMESTAMP_CANDIDATES = [
    "RecordingTime",
    "Recording Time",
    "recording_time",
    "Timestamp",
    "timestamp",
]


def find_timestamp_column(df):
    for column in TIMESTAMP_CANDIDATES:
        if column in df.columns:
            return column

    # Fallback: identify a column whose name contains time or timestamp.
    for column in df.columns:
        name = str(column).lower()
        if "recordingtime" in name or "timestamp" in name:
            return column

    return None


def clean_file(filename):
    input_path = RAW_DIR / filename
    output_path = PROCESSED_DIR / filename.replace(".csv", "_clean.csv")

    print(f"\n{'=' * 70}")
    print(f"Processing: {filename}")

    df = pd.read_csv(
        input_path,
        sep=";",
        decimal=",",
        na_values=["\\N", "N/A", ""],
        encoding="utf-8-sig",
        low_memory=False,
    )

    original_rows = len(df)
    timestamp_col = find_timestamp_column(df)

    if timestamp_col is None:
        print("WARNING: No timestamp column identified.")
    else:
        df[timestamp_col] = pd.to_datetime(
            df[timestamp_col],
            errors="coerce",
            dayfirst=False,
        )

        invalid_timestamps = df[timestamp_col].isna().sum()
        print(f"Timestamp column: {timestamp_col}")
        print(f"Invalid/missing timestamps: {invalid_timestamps}")

        # Sort only when timestamps were successfully parsed.
        df = df.sort_values(timestamp_col, na_position="last")

        duplicate_timestamps = df[timestamp_col].duplicated().sum()
        print(f"Duplicate timestamps: {duplicate_timestamps}")

        # Do not drop duplicate timestamps automatically; they may be valid telemetry.
        # Do not drop rows with invalid timestamps automatically either.

    # Convert columns that are numeric-looking, while preserving text/status fields.
    for column in df.columns:
        if column == timestamp_col:
            continue

        converted = pd.to_numeric(df[column], errors="coerce")

        non_missing_original = df[column].notna().sum()
        numeric_success = converted.notna().sum()

        # Convert only if most populated values are numeric.
        if non_missing_original > 0 and numeric_success / non_missing_original >= 0.80:
            df[column] = converted

    df.to_csv(output_path, index=False)

    print(f"Rows: {original_rows}")
    print(f"Columns: {df.shape[1]}")
    print(f"Saved: {output_path}")

    print("\nTop columns by missing-value count:")
    missing = df.isna().sum().sort_values(ascending=False)
    print(missing[missing > 0].head(15).to_string() or "No missing values")

    if timestamp_col and df[timestamp_col].notna().any():
        print(f"\nTime range: {df[timestamp_col].min()} -> {df[timestamp_col].max()}")

    print("\nSample:")
    print(df.head(3).to_string(index=False))


def main():
    for filename in APID_FILES:
        path = RAW_DIR / filename

        if not path.exists():
            print(f"\nSkipping missing file: {path}")
            continue

        clean_file(filename)


if __name__ == "__main__":
    main()