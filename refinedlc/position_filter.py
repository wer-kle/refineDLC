#!/usr/bin/env python3
"""
position_filter.py

Filters DeepLabCut data based on positional changes between consecutive frames.
If the change in position for a body part exceeds a user-defined threshold, the coordinates are set to NaN.
Supports single-file or batch-directory processing.

Usage:
    # Single-file mode
    python position_filter.py \
        --input likelihood_filtered.csv \
        --output position_filtered.csv \
        --method euclidean \
        --threshold 30

    # Batch-directory mode
    python position_filter.py \
        --input-dir path/to/likelihood_filtered_csvs/ \
        --output-dir path/to/position_filtered_csvs/ \
        --method euclidean \
        --threshold 30
"""

import argparse
import logging
import pandas as pd
import numpy as np
import os
import glob
from pathlib import Path


def position_filter(input_file: str, output_file: str, method: str, threshold: float):
    logging.info("Loading data from %s", input_file)
    try:
        data = pd.read_csv(input_file)
    except Exception as e:
        logging.error("Failed to load input file %s: %s", input_file, e)
        raise

    body_parts = set(col.rsplit('_', 1)[0] for col in data.columns if col.endswith('_x'))
    for part in body_parts:
        x_col = f"{part}_x"
        y_col = f"{part}_y"
        if x_col not in data.columns or y_col not in data.columns:
            continue

        logging.info("Filtering positional changes for body part: %s", part)
        x = data[x_col].to_numpy()
        y = data[y_col].to_numpy()
        if method == 'euclidean':
            diff = np.sqrt(np.diff(x)**2 + np.diff(y)**2)
        elif method == 'x':
            diff = np.abs(np.diff(x))
        elif method == 'y':
            diff = np.abs(np.diff(y))
        else:
            logging.error("Invalid method: %s. Use 'euclidean', 'x', or 'y'.", method)
            raise ValueError(f"Invalid method: {method}")

        diff = np.insert(diff, 0, 0)
        mask = diff > threshold
        data.loc[mask, x_col] = pd.NA
        data.loc[mask, y_col] = pd.NA
        logging.info("For body part %s, filtered %d frames based on positional change.", part, mask.sum())

    logging.info("Saving position-filtered data to %s", output_file)
    data.to_csv(output_file, index=False)
    logging.info("Position filtering completed for %s.", input_file)


def process_file(input_path: str, output_dir: str, method: str, threshold: float):
    """Helper: apply filtering to a single CSV and save it into the output directory."""
    filename = Path(input_path).name
    output_path = Path(output_dir) / filename
    position_filter(str(input_path), str(output_path), method, threshold)


def main():
    parser = argparse.ArgumentParser(
        description="Filter DeepLabCut data by positional change in single or batch mode."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--input', help="Path to a single CSV file with likelihood-filtered data.")
    group.add_argument('--input-dir', help="Directory containing CSV files to filter.")

    parser.add_argument('--output', help="Path to save single output CSV.")
    parser.add_argument('--output-dir', help="Directory to save batch output CSVs.")
    parser.add_argument(
        '--method', choices=['euclidean', 'x', 'y'], required=True,
        help="Filtering method: 'euclidean', 'x', or 'y'."
    )
    parser.add_argument(
        '--threshold', type=float, required=True,
        help="Threshold for positional change (in pixels)."
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    if args.input:
        if not args.output:
            parser.error('--output is required when using --input')
        position_filter(args.input, args.output, args.method, args.threshold)
    else:
        if not args.output_dir:
            parser.error('--output-dir is required when using --input-dir')
        os.makedirs(args.output_dir, exist_ok=True)

        pattern = os.path.join(args.input_dir, '*.csv')
        files = glob.glob(pattern)
        logging.info("Found %d CSV files in %s", len(files), args.input_dir)
        for file_path in files:
            logging.info("Processing file %s", file_path)
            process_file(file_path, args.output_dir, args.method, args.threshold)


if __name__ == "__main__":
    main()
