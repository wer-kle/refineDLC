#!/usr/bin/env python3
"""
position_filter.py

Filters DeepLabCut CSV outputs by removing non-organic outliers in positional changes
between consecutive frames. Supports fixed-threshold filtering and robust statistical
outlier detection via modified Z-score (MAD), IQR fences, or standard Z-score (mean ± k·SD).

Key features:
  - Single-file or batch-directory processing
  - Choice of difference metric: euclidean (default), x-axis, or y-axis changes
  - Fixed threshold mode (--threshold)
  - Robust mode (--stat-method = mad|iqr|std) with tunable cutoffs

Usage examples:
  # Fixed threshold (simple):
  python position_filter.py \
      --input-dir dlc_csvs/ --output-dir cleaned_csvs/ \
      --method euclidean --threshold 30

  # Robust MAD in batch:
  python position_filter.py \
      --input-dir dlc_csvs/ --output-dir cleaned_csvs/ \
      --method euclidean --stat-method mad --mad-threshold 3.5

  # Single file with IQR fences:
  python position_filter.py \
      --input in.csv --output out.csv \
      --method x --stat-method iqr --iqr-multiplier 2.0

  # Robust standard-deviation Z-score:
  python position_filter.py \
      --input file.csv --output out.csv \
      --method y --stat-method std --std-threshold 3.0
"""

import argparse
import logging
import os
import glob
from pathlib import Path
import numpy as np
import pandas as pd


def detect_outliers(diff: np.ndarray,
                    stat_method: str = 'mad',
                    mad_threshold: float = 3.5,
                    iqr_multiplier: float = 1.5,
                    std_threshold: float = 3.0) -> np.ndarray:
    """
    Return boolean mask for outliers in diff array.
    Pads first frame with 0-change, then applies:
      - 'mad': modified Z-score > mad_threshold
      - 'iqr': values outside [Q1 - m*IQR, Q3 + m*IQR]
      - 'std': Z-score > std_threshold based on mean and standard deviation
    """
    # prepend zero change for first frame
    diff_full = np.insert(diff, 0, 0.0)

    if stat_method == 'mad':
        med = np.median(diff_full)
        mad = np.median(np.abs(diff_full - med))
        mad = mad if mad else np.finfo(float).eps
        mod_z = 0.6745 * (diff_full - med) / mad
        return np.abs(mod_z) > mad_threshold

    elif stat_method == 'iqr':
        q1, q3 = np.percentile(diff_full, [25, 75])
        iqr = q3 - q1
        lower, upper = q1 - iqr_multiplier * iqr, q3 + iqr_multiplier * iqr
        return (diff_full < lower) | (diff_full > upper)

    elif stat_method == 'std':
        mean = np.mean(diff_full)
        std = np.std(diff_full)
        std = std if std else np.finfo(float).eps
        z_scores = (diff_full - mean) / std
        return np.abs(z_scores) > std_threshold

    else:
        raise ValueError(f"Unknown stat_method '{stat_method}'")


def position_filter(infile: str,
                    outfile: str,
                    method: str,
                    mode: str,
                    threshold: float = None,
                    mad_threshold: float = None,
                    iqr_multiplier: float = None,
                    std_threshold: float = None):
    """
    Load CSV, detect outliers in positional jumps per bodypart,
    and set those X/Y pairs to NaN. Save cleaned CSV.

    mode: 'threshold' or one of 'mad','iqr','std'
    threshold: float for fixed mode
    mad_threshold: float for MAD-based robust mode
    iqr_multiplier: float for IQR-based robust mode
    std_threshold: float for standard-deviation robust mode
    """
    logging.info(f"Loading data: {infile}")
    df = pd.read_csv(infile)
    parts = {col.rsplit('_', 1)[0] for col in df.columns if col.endswith('_x')}

    for part in sorted(parts):
        xcol, ycol = f"{part}_x", f"{part}_y"
        if xcol not in df or ycol not in df:
            continue
        logging.info(f"  Processing '{part}' using method={method}, mode={mode}")
        x = df[xcol].to_numpy(dtype=float)
        y = df[ycol].to_numpy(dtype=float)
        # compute differences
        if method == 'euclidean':
            diffs = np.sqrt(np.diff(x)**2 + np.diff(y)**2)
        elif method == 'x':
            diffs = np.abs(np.diff(x))
        elif method == 'y':
            diffs = np.abs(np.diff(y))
        else:
            raise ValueError(f"Invalid method '{method}'")

        if mode == 'threshold':
            mask = np.insert(diffs > threshold, 0, False)
        else:
            # robust mode uses detect_outliers
            mask = detect_outliers(
                diffs,
                stat_method=mode,
                mad_threshold=mad_threshold,
                iqr_multiplier=iqr_multiplier,
                std_threshold=std_threshold
            )

        df.loc[mask, xcol] = pd.NA
        df.loc[mask, ycol] = pd.NA
        logging.info(f"    Removed {mask.sum()} outlier frames for '{part}'")

    os.makedirs(Path(outfile).parent or '.', exist_ok=True)
    logging.info(f"Saving cleaned data to {outfile}")
    df.to_csv(outfile, index=False)


def main():
    p = argparse.ArgumentParser(
        description="Filter DLC data by positional change (fixed or robust methods)"
    )
    grp = p.add_mutually_exclusive_group(required=True)
    grp.add_argument('--input', help="Single input CSV file")
    grp.add_argument('--input-dir', help="Directory of CSV files to filter")

    p.add_argument('--output', help="Single output CSV file path")
    p.add_argument('--output-dir', help="Directory to save batch output CSVs")

    p.add_argument('--method', choices=['euclidean','x','y'], required=True,
                   help="Difference metric: euclidean, x, or y")

    det = p.add_mutually_exclusive_group(required=True)
    det.add_argument('--threshold', type=float,
                     help="Fixed threshold for positional change")
    det.add_argument('--stat-method', choices=['mad','iqr','std'],
                     help="Robust outlier detection via 'mad', 'iqr', or 'std'")

    p.add_argument('--mad-threshold', type=float, default=3.5,
                   help="Modified-Z cutoff if using --stat-method mad (default 3.5)")
    p.add_argument('--iqr-multiplier', type=float, default=1.5,
                   help="IQR multiplier if using --stat-method iqr (default 1.5)")
    p.add_argument('--std-threshold', type=float, default=3.0,
                   help="Z-score cutoff if using --stat-method std (default 3.0)")

    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Determine mode
    if args.threshold is not None:
        mode = 'threshold'
    else:
        mode = args.stat_method

    # Single-file
    if args.input:
        if not args.output:
            p.error("--output is required with --input")
        position_filter(
            args.input, args.output,
            args.method, mode,
            threshold=args.threshold,
            mad_threshold=args.mad_threshold,
            iqr_multiplier=args.iqr_multiplier,
            std_threshold=args.std_threshold
        )
    else:
        if not args.output_dir:
            p.error("--output-dir is required with --input-dir")
        os.makedirs(args.output_dir, exist_ok=True)
        pattern = os.path.join(args.input_dir, "*.csv")
        files = glob.glob(pattern)
        logging.info(f"Found {len(files)} CSV(s) in {args.input_dir}")
        for infile in sorted(files):
            outfile = os.path.join(args.output_dir, Path(infile).name)
            position_filter(
                infile, outfile,
                args.method, mode,
                threshold=args.threshold,
                mad_threshold=args.mad_threshold,
                iqr_multiplier=args.iqr_multiplier,
                std_threshold=args.std_threshold
            )


if __name__ == "__main__":
    main()
