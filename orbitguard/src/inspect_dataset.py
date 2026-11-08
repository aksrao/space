from pathlib import Path
import csv
from collections import Counter

DATA_DIR = Path("data/B2")

for file in sorted(DATA_DIR.glob("*.csv")):
    print(f"\n{'=' * 60}")
    print(f"FILE: {file.name}")

    # Detect likely delimiter from the header
    with file.open("r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(8192)

    delimiter = ";" if sample.splitlines()[0].count(";") > sample.splitlines()[0].count(",") else ","
    print(f"Detected delimiter: {repr(delimiter)}")

    # Check whether rows have a consistent number of fields
    field_counts = Counter()
    malformed_examples = []

    try:
        with file.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f, delimiter=delimiter)
            expected_fields = None

            for row_number, row in enumerate(reader, start=1):
                if not row:
                    continue

                if expected_fields is None:
                    expected_fields = len(row)

                field_counts[len(row)] += 1

                if len(row) != expected_fields and len(malformed_examples) < 5:
                    malformed_examples.append(
                        (row_number, len(row), row[:4])
                    )

        print(f"Expected fields per row: {expected_fields}")
        print(f"Field-count distribution: {dict(field_counts)}")

        if malformed_examples:
            print("Rows with unexpected field counts:")
            for example in malformed_examples:
                print(example)
        else:
            print("Field counts are consistent.")

    except Exception as e:
        print(f"CSV parsing error: {e}")