#!/usr/bin/env python3
"""
clean_coordinates.py

Cleans DeepLabCut coordinate data by:
- Inverting y-coordinates (making them negative, for plotting)
- Removing rows with all zero values (corrupted frames)
- Excluding specified irrelevant body parts
- Batch‑processing a directory of CSVs
"""

import argparse
import logging
import pandas as pd
import os
from pathlib import Path
import glob


def clean_coordinates(input_file: str, output_file: str, exclude_parts: str):
    logging.info("Loading DLC data from %s", input_file)
    # 1) Read all three header rows so we capture bodypart+coord
    df = pd.read_csv(input_file, header=[0, 1, 2])

    # 2) Flatten MultiIndex: drop the scorer level, join bodypart+coord
    df.columns = [
        f"{bp.strip()}_{coord.strip()}"
        for (_, bp, coord) in df.columns
    ]

    # 3) Invert y columns by multiplying by -1
    y_cols = [c for c in df.columns if c.lower().endswith('_y')]
    if not y_cols:
        logging.warning("No '_y' columns found—check your headers!")
    for col in y_cols:
        logging.info("Flipping sign of %s", col)
        df[col] = -df[col]

    # 4) Drop rows where *all* coordinate columns are zero
    coord_cols = [c for c in df.columns if '_' in c]
    before = len(df)
    df = df.loc[~(df[coord_cols] == 0).all(axis=1)]
    logging.info("Removed %d all‑zero rows", before - len(df))

    # 5) Exclude any bodyparts the user requested
    if exclude_parts:
        parts = [p.strip() for p in exclude_parts.split(',')]
        for p in parts:
            drops = [c for c in df.columns if c.startswith(p + "_")]
            if drops:
                df.drop(columns=drops, inplace=True)
                logging.info("Dropped columns for %s: %s", p, drops)

    # 6) Write out
    out_dir = os.path.dirname(output_file)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    df.to_csv(output_file, index=False)
    logging.info("Saved cleaned data to %s", output_file)


def process_file(inf, out_dir, exclude_parts):
    name = Path(inf).name
    clean_coordinates(inf, str(Path(out_dir)/name), exclude_parts)


def main():
    p = argparse.ArgumentParser(
        description="Clean DeepLabCut CSVs (invert y, drop zeros, exclude parts)."
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--input',     help="Single input CSV")
    g.add_argument('--input-dir', help="Directory of CSVs")

    p.add_argument('--output',     help="Single output CSV (with --input)")
    p.add_argument('--output-dir', help="Output directory (with --input-dir)")
    p.add_argument('--exclude',    default="", help="Comma‑sep list of bodyparts")
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    if args.input:
        if not args.output:
            p.error('--output is required with --input')
        clean_coordinates(args.input, args.output, args.exclude)
    else:
        if not args.output_dir:
            p.error('--output-dir is required with --input-dir')
        os.makedirs(args.output_dir, exist_ok=True)
        for f in glob.glob(os.path.join(args.input_dir, '*.csv')):
            logging.info("Processing %s", f)
            process_file(f, args.output_dir, args.exclude)


if __name__ == "__main__":
    main()
