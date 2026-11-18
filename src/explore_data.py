from pathlib import Path
import pandas as pd

project_dir = Path(__file__).resolve().parent.parent
data_dir = project_dir / "data" / "raw"

csv_files = list(data_dir.glob("*.csv"))

for file in csv_files:
    df = pd.read_csv(file)

    print(f"\n{'=' * 50}")
    print(f"DATASET: {file.name}")
    print(f"Shape: {df.shape}")

    print("\nData types:")
    print(df.dtypes)

    print("\nMissing values:")
    print(df.isnull().sum())

    print("\nDuplicate rows:")
    print(df.duplicated().sum())