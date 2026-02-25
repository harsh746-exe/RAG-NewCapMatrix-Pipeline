#!/usr/bin/env python3
"""
Convert the LEAD I&M capability matrix template into the RAG requirements matrix.

Usage:
  python3 convert_template_to_requirements.py \
    --input "data/inputs/Capabilities Matrix_LEAD I and M_Partner Template (1).xlsx"

This script:
  - Reads the template Excel (with 'RFP Requirements' as the first column header)
  - Extracts the requirements rows under that header
  - Writes `data/outputs/requirements_matrix.xlsx` in the format expected by the RAG pipeline
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd


# Make src/ importable (same pattern as main.py)
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from config.settings import Config  # noqa: E402


def build_requirements_from_template(input_path: Path, output_path: Path) -> None:
    if not input_path.exists():
        raise FileNotFoundError(f"Input template not found: {input_path}")

    # Read raw with no header so we can locate the real header row
    df_raw = pd.read_excel(input_path, header=None, engine="openpyxl")

    # Find the row where the first column equals "RFP Requirements"
    header_matches = df_raw.index[df_raw.iloc[:, 0] == "RFP Requirements"].tolist()
    if not header_matches:
        raise ValueError("Could not find a row with 'RFP Requirements' in the first column.")

    header_row_idx = header_matches[0]

    # Data rows start after this header row; first column contains the requirement text
    requirements_series = df_raw.iloc[header_row_idx + 1 :, 0]

    # Build clean DataFrame
    req_df = pd.DataFrame({"Requirements": requirements_series})
    # Drop empty / NaN rows
    req_df["Requirements"] = req_df["Requirements"].astype(str).str.strip()
    req_df = req_df[req_df["Requirements"].notna() & (req_df["Requirements"] != "nan") & (req_df["Requirements"] != "")]

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    req_df.to_excel(output_path, index=False, engine="openpyxl")
    print(f"Requirements matrix written to: {output_path}")
    print(f"Total requirements: {len(req_df)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert LEAD I&M capability matrix template into requirements_matrix.xlsx")
    parser.add_argument(
        "--input",
        type=str,
        default=str(PROJECT_ROOT / "data" / "inputs" / "Capabilities Matrix_LEAD I and M_Partner Template (1).xlsx"),
        help="Path to the capability matrix template Excel file.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(Config.EXCEL_PATH),
        help="Path to write the requirements matrix Excel (defaults to Config.EXCEL_PATH).",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    build_requirements_from_template(input_path, output_path)


if __name__ == "__main__":
    main()

