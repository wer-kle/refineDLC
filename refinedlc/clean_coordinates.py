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

    # --- 1) Read the three header rows so we get a true MultiIndex --- #
    try:
        raw = pd.read_csv(input_file, header=[0, 1, 2])
    except Exception as e:
        logging.error("Failed to load input file %s: %s", input_file, e)
        raise

    # --- 2) Flatten the MultiIndex to simple names like "left_eye_x", "left_eye_y" --- #
    #     We drop the first level (scorer/model) and join the bodypart + coord.
    raw.columns = [
        f"{bodypart.strip()}_{coord.strip()}"
        for (_, bodypart, coord) in raw.columns
    ]

    data = raw.copy()  # now data.columns are strings ending in "_x", "_y", or "_likelihood"

    # --- 3) Detect all '_y' columns and invert via max_y - y --- #
    y_cols = [c for c in data.columns if c.lower().endswith('_y')]
    if not y_cols:
        logging.warning("No '_y' columns found to invert.")
    else:
        for col in y_cols:
            max_y = data[col].max()
            logging.info("Inverting y in column %s (max_y=%s)", col, max_y)
            data[col] = max_y - data[col]

    # --- 4) Remove rows where *all* coordinate columns are zero --- #
    coord_cols = [c for c in data.columns if '_' in c]
    before = len(data)
    data = data.loc[~(data[coord_cols] == 0).all(axis=1)]
    logging.info("Removed %d all‐zero rows", before - len(data))

    # --- 5) Drop any bodyparts the user wants to exclude --- #
    if exclude_parts:
        to_exclude = [p.strip() for p in exclude_parts.split(',')]
        logging.info("Excluding parts: %s", to_exclude)
        for part in to_exclude:
            drops = [c for c in data.columns if c.startswith(part + "_")]
            if drops:
                data.drop(columns=drops, inplace=True, errors='ignore')
                logging.info("Dropped columns: %s", drops)

    # --- 6) Write out --- #
    out_dir = os.path.dirname(output_file)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    logging.info("Saving cleaned data to %s", output_file)
    data.to_csv(output_file, index=False)
    logging.info("Done cleaning %s", input_file)


def process_file(input_path: str, output_dir: str, exclude_parts: str):
    filename = Path(input_path).name
    clean_coordinates(str(input_path), str(Path(output_dir) / filename), exclude_parts)


def main():
    parser = argparse.ArgumentParser(
        description="Clean DeepLabCut coordinate data in single or batch mode."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--input',     help="Path to a single input CSV file.")
    group.add_argument('--input-dir', help="Path to a directory of CSVs.")

    parser.add_argument('--output',     help="Output CSV (with --input).")
    parser.add_argument('--output-dir', help="Output directory (with --input-dir).")
    parser.add_argument('--exclude',    default="", help="Comma‑sep list of bodyparts to drop.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    if args.input:
        if not args.output:
            parser.error('--output is required with --input')
        clean_coordinates(args.input, args.output, args.exclude)
    else:
        if not args.output_dir:
            parser.error('--output-dir is required with --input-dir')
        os.makedirs(args.output_dir, exist_ok=True)
        files = glob.glob(os.path.join(args.input_dir, '*.csv'))
        logging.info("Found %d files in %s", len(files), args.input_dir)
        for f in files:
            logging.info("Processing %s", f)
            process_file(f, args.output_dir, args.exclude)


if __name__ == "__main__":
    main()
