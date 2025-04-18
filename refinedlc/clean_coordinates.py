#!/usr/bin/env python3
"""
clean_coordinates.py

Cleans DeepLabCut coordinate data by:
- Inverting y-coordinates (to transform the image-based coordinate system)
- Removing rows with all zero values (indicative of corrupted frames)
- Excluding specified irrelevant body parts
- Iterating over a directory of CSV files if desired
"""

import argparse
import logging
import pandas as pd
import os
from pathlib import Path
import glob


def clean_coordinates(input_file: str, output_file: str, exclude_parts: str):
    logging.info("Loading data from %s", input_file)
    try:
        data = pd.read_csv(input_file)
    except Exception as e:
        logging.error("Failed to load input file %s: %s", input_file, e)
        raise

    # Invert y-coordinates by multiplying by -1
    y_columns = [col for col in data.columns if col.endswith('_y')]
    for col in y_columns:
        logging.info("Inverting y-coordinates in column %s", col)
        data[col] = -data[col]

    # Remove rows where all coordinate values are zero
    coord_columns = [col for col in data.columns if '_' in col]
    initial_count = len(data)
    data = data.loc[~(data[coord_columns] == 0).all(axis=1)]
    removed = initial_count - len(data)
    logging.info("Removed %d zero-value rows", removed)

    # Exclude irrelevant body parts
    if exclude_parts:
        exclude_list = [part.strip() for part in exclude_parts.split(',')]
        logging.info("Excluding body parts: %s", exclude_list)
        for part in exclude_list:
            cols_to_drop = [col for col in data.columns if col.startswith(part)]
            if cols_to_drop:
                data.drop(columns=cols_to_drop, inplace=True, errors='ignore')
                logging.info("Dropped columns: %s", cols_to_drop)

    # Ensure output directory exists
    out_dir = os.path.dirname(output_file)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    logging.info("Saving cleaned data to %s", output_file)
    data.to_csv(output_file, index=False)
    logging.info("Data cleaning for %s completed.", input_file)


def process_file(input_path: str, output_dir: str, exclude_parts: str):
    """Helper to clean a single CSV and save it into the output directory."""
    filename = Path(input_path).name
    output_path = Path(output_dir) / filename
    clean_coordinates(str(input_path), str(output_path), exclude_parts)


def main():
    parser = argparse.ArgumentParser(description="Clean DeepLabCut coordinate data in single or batch mode.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--input', help="Path to a single input CSV file.")
    group.add_argument('--input-dir', help="Path to a directory containing CSV files.")

    parser.add_argument('--output', help="Path to a single output CSV file (with --input). ")
    parser.add_argument('--output-dir', help="Directory to save cleaned CSVs (with --input-dir). ")
    parser.add_argument('--exclude', default="", help="Comma-separated list of body parts to exclude.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    if args.input:
        if not args.output:
            parser.error('--output is required when using --input')
        clean_coordinates(args.input, args.output, args.exclude)
    else:
        if not args.output_dir:
            parser.error('--output-dir is required when using --input-dir')
        os.makedirs(args.output_dir, exist_ok=True)

        pattern = os.path.join(args.input_dir, '*.csv')
        files = glob.glob(pattern)
        logging.info("Found %d CSV files in %s", len(files), args.input_dir)

        for file_path in files:
            logging.info("Processing file %s", file_path)
            process_file(file_path, args.output_dir, args.exclude)


if __name__ == "__main__":
    main()
