#!/usr/bin/env python3
"""
likelihood_filter.py

Filters DeepLabCut data based on likelihood scores.
Low likelihood values (below a threshold specified by user) result in NaNs **only** in coordinate columns; likelihood values are retained.
Supports single-file or batch-directory processing.

Usage:
    # Single-file mode
    python likelihood_filter.py \
        --input cleaned_data.csv \
        --output likelihood_filtered.csv \
        --threshold 0.6

    # Batch-directory mode
    python likelihood_filter.py \
        --input-dir path/to/cleaned_csvs/ \
        --output-dir path/to/likelihood_filtered_csvs/ \
        --threshold 0.6
"""

import argparse
import logging
import pandas as pd
import os
import glob
from pathlib import Path


def likelihood_filter(input_file: str, output_file: str, threshold: float):
    logging.info("Loading data from %s", input_file)
    try:
        data = pd.read_csv(input_file)
    except Exception as e:
        logging.error("Failed to load input file %s: %s", input_file, e)
        raise

    # Identify likelihood columns (assume naming: <bodypart>_likelihood)
    likelihood_cols = [col for col in data.columns if col.endswith('_likelihood')]
    if not likelihood_cols:
        logging.warning("No likelihood columns found in %s. Saving unchanged.", input_file)
        data.to_csv(output_file, index=False)
        return

    for col in likelihood_cols:
        logging.info("Applying threshold filter on %s (threshold=%.2f)", col, threshold)
        # Create mask for low-likelihood frames; keep likelihood values untouched
        mask = data[col] < threshold
        base = col[:-len('_likelihood')]
        # Only set coordinate columns to NaN
        for suffix in ['_x', '_y']:
            coord_col = f"{base}{suffix}"
            if coord_col in data.columns:
                logging.debug("Setting NaN for %s in %d frames", coord_col, mask.sum())
                data.loc[mask, coord_col] = pd.NA

    logging.info("Saving likelihood-filtered data to %s", output_file)
    data.to_csv(output_file, index=False)
    logging.info("Likelihood filtering completed for %s.", input_file)


def process_file(input_path: str, output_dir: str, threshold: float):
    """Helper: apply filtering to a single file and save in output directory."""
    filename = Path(input_path).name
    output_path = Path(output_dir) / filename
    likelihood_filter(str(input_path), str(output_path), threshold)


def main():
    parser = argparse.ArgumentParser(
        description="Filter DeepLabCut data by likelihood in single or batch mode."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--input', help="Path to a single cleaned CSV file.")
    group.add_argument('--input-dir', help="Path to a directory of cleaned CSV files.")

    parser.add_argument('--output', help="Path to save single output CSV.")
    parser.add_argument('--output-dir', help="Directory to save batch outputs.")
    parser.add_argument(
        '--threshold', type=float, required=True,
        help="Likelihood threshold below which coordinates are set to NaN."
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    if args.input:
        if not args.output:
            parser.error('--output is required when using --input')
        likelihood_filter(args.input, args.output, args.threshold)
    else:
        if not args.output_dir:
            parser.error('--output-dir is required when using --input-dir')
        os.makedirs(args.output_dir, exist_ok=True)

        pattern = os.path.join(args.input_dir, '*.csv')
        files = glob.glob(pattern)
        logging.info("Found %d CSV files in %s", len(files), args.input_dir)
        for file_path in files:
            logging.info("Processing file %s", file_path)
            process_file(file_path, args.output_dir, args.threshold)


if __name__ == "__main__":
    main()
