#!/usr/bin/env python3
"""
position_filter.py

Filters DeepLabCut CSV outputs by removing non-organic outliers in positional changes
between consecutive frames. Supports:
  - Fixed-threshold filtering
  - Robust statistical outlier detection via modified Z-score (MAD), IQR fences (with
    optional skew adjustment), or standard Z-score (mean ± k·SD)
  - Percentile-based trimming
  - Optional log-transformation of the positional changes before outlier detection

Key features:
  - Single-file or batch-directory processing
  - Choice of difference metric: euclidean (default), x-axis, or y-axis changes
  - Fixed threshold mode (--threshold)
  - Robust mode (--stat-method = mad|iqr|adj_iqr|std)
  - Percentile trimming mode (--percentile)
  - Optional log-transform of diffs before robust detection (--log-transform)

Usage examples:
  # 1) Fixed threshold (simple):
  python position_filter.py \
      --input-dir dlc_csvs/ --output-dir cleaned_csvs/ \
      --method euclidean --threshold 30

  # 2) Robust MAD in batch, with log-transform:
  python position_filter.py \
      --input-dir dlc_csvs/ --output-dir cleaned_csvs/ \
      --method euclidean --stat-method mad --mad-threshold 3.5 \
      --log-transform

  # 3) Single file with classical IQR fences:
  python position_filter.py \
      --input in.csv --output out.csv \
      --method x --stat-method iqr --iqr-multiplier 2.0

  # 4) Single file with skew-adjusted IQR (Hubert & Vandervieren) on raw diffs:
  python position_filter.py \
      --input coords.csv --output coords_cleaned.csv \
      --method y --stat-method adj_iqr --iqr-multiplier 1.5

  # 5) Percentile trimming (manually remove > 99th percentile):
  python position_filter.py \
      --input file.csv --output out.csv \
      --method euclidean --percentile 99.0

  # 6) Robust std Z-score, without log-transform:
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

# For skew-adjusted IQR (medcouple)
try:
    from statsmodels.stats.stattools import medcouple
except ImportError:
    raise ImportError("statsmodels is required for 'adj_iqr' mode. Install via 'pip install statsmodels'.")


def detect_outliers(diff_full: np.ndarray,
                    stat_method: str = 'mad',
                    mad_threshold: float = 3.5,
                    iqr_multiplier: float = 1.5,
                    std_threshold: float = 3.0,
                    percentile: float = None,
                    skew_adjust: bool = False) -> np.ndarray:
    """
    Return boolean mask for outliers in diff_full array (length = n_frames).
    Assumes diff_full already has length = n_frames (first entry = 0).
    Modes:
      - 'mad': modified Z-score > mad_threshold
      - 'iqr': classical IQR fences: [Q1 - m*IQR, Q3 + m*IQR]
      - 'adj_iqr': skew-adjusted IQR (Hubert & Vandervieren) using medcouple
      - 'std': Z-score > std_threshold based on mean and standard deviation
      - 'percentile': remove any value > percentile-th percentile
    """
    # Only consider non-NaN values when computing medians, quartiles, etc.
    diff_valid = diff_full[~np.isnan(diff_full)]

    if stat_method == 'mad':
        med = np.median(diff_valid)
        mad = np.median(np.abs(diff_valid - med))
        mad = mad if mad != 0.0 else np.finfo(float).eps

        # Convert MAD-based Z-cutoff back to raw thresholds for logging
        upper_cut = med + (mad_threshold * mad / 0.6745)
        lower_cut = med - (mad_threshold * mad / 0.6745)
        logging.info(f"MAD-based thresholds for displacements: lower={lower_cut:.6f}, upper={upper_cut:.6f}")

        mod_z = 0.6745 * (diff_full - med) / mad
        return np.abs(mod_z) > mad_threshold

    elif stat_method == 'iqr':
        q1, q3 = np.nanpercentile(diff_full, [25, 75])
        iqr = q3 - q1

        lower = q1 - iqr_multiplier * iqr
        upper = q3 + iqr_multiplier * iqr
        logging.info(f"IQR-based thresholds for displacements: lower={lower:.6f}, upper={upper:.6f} (multiplier={iqr_multiplier})")

        return (diff_full < lower) | (diff_full > upper)

    elif stat_method == 'adj_iqr':
        q1, q3 = np.nanpercentile(diff_full, [25, 75])
        iqr = q3 - q1

        MC = medcouple(diff_valid)
        if MC >= 0:
            factor_lower = np.exp(-4 * MC)
            factor_upper = np.exp(3 * MC)
        else:
            factor_lower = np.exp(-3 * MC)
            factor_upper = np.exp(4 * MC)

        lower = q1 - iqr_multiplier * factor_lower * iqr
        upper = q3 + iqr_multiplier * factor_upper * iqr
        logging.info(f"Skew-adjusted IQR thresholds for displacements: lower={lower:.6f}, upper={upper:.6f} (multiplier={iqr_multiplier}, MC={MC:.6f})")

        return (diff_full < lower) | (diff_full > upper)

    elif stat_method == 'std':
        mean = np.nanmean(diff_full)
        std = np.nanstd(diff_full)
        std = std if std != 0.0 else np.finfo(float).eps

        lower = mean - std_threshold * std
        upper = mean + std_threshold * std
        logging.info(f"STD-based thresholds for displacements: lower={lower:.6f}, upper={upper:.6f} (std_threshold={std_threshold})")

        z_scores = (diff_full - mean) / std
        return np.abs(z_scores) > std_threshold

    elif stat_method == 'percentile':
        cut = np.nanpercentile(diff_full, percentile)
        logging.info(f"Percentile-based threshold: cutoff at {percentile}th percentile = {cut:.6f}")
        return diff_full > cut

    else:
        raise ValueError(f"Unknown stat_method '{stat_method}'")


def position_filter(infile: str,
                    outfile: str,
                    method: str,
                    mode: str,
                    threshold: float = None,
                    mad_threshold: float = None,
                    iqr_multiplier: float = None,
                    std_threshold: float = None,
                    percentile: float = None,
                    log_transform: bool = False):
    """
    Load CSV, detect outliers in positional jumps per bodypart,
    and set those X/Y pairs to NaN. Save cleaned CSV.

    mode: 'threshold', 'mad', 'iqr', 'adj_iqr', 'std', or 'percentile'
    threshold: float for fixed threshold mode
    mad_threshold: float for MAD-based robust mode
    iqr_multiplier: float for IQR/adj_IQR-based robust mode
    std_threshold: float for standard-deviation robust mode
    percentile: float between 0 and 100 for percentile trimming
    log_transform: whether to apply log(diffs + δ) before robust detection
    """
    logging.info(f"Loading data: {infile}")
    df = pd.read_csv(infile)
    # Identify all tracked parts (columns ending with '_x' and '_y')
    parts = {col.rsplit('_', 1)[0] for col in df.columns if col.endswith('_x')}

    for part in sorted(parts):
        xcol, ycol = f"{part}_x", f"{part}_y"
        if xcol not in df.columns or ycol not in df.columns:
            continue

        logging.info(f"  Processing '{part}' | method={method}, mode={mode}, log_transform={log_transform}")
        x = df[xcol].to_numpy(dtype=float)
        y = df[ycol].to_numpy(dtype=float)

        # Compute per-frame diffs according to chosen metric
        if method == 'euclidean':
            raw_diffs = np.sqrt(np.diff(x, prepend=x[0])**2 + np.diff(y, prepend=y[0])**2)
        elif method == 'x':
            raw_diffs = np.abs(np.diff(x, prepend=x[0]))
        elif method == 'y':
            raw_diffs = np.abs(np.diff(y, prepend=y[0]))
        else:
            raise ValueError(f"Invalid method '{method}'")

        # For fixed-threshold mode: compare raw_diffs > threshold
        if mode == 'threshold':
            if threshold is None:
                raise ValueError("Fixed-threshold mode requires --threshold")
            mask = raw_diffs > threshold

        else:
            # Robust or percentile mode. Optionally log-transform first.
            if log_transform:
                # Shift by a small delta to avoid log(0)
                delta = 1e-8
                diffs = np.log(raw_diffs + delta)
            else:
                diffs = raw_diffs.copy()

            # diffs_full already has length = n_frames since we used prepend in np.diff
            diffs_full = diffs

            # Detect outliers on diffs_full
            mask = detect_outliers(
                diff_full=diffs_full,
                stat_method=mode,
                mad_threshold=mad_threshold,
                iqr_multiplier=iqr_multiplier,
                std_threshold=std_threshold,
                percentile=percentile
            )

        # Set flagged X/Y pairs to NaN
        removed_count = int(mask.sum())
        df.loc[mask, xcol] = pd.NA
        df.loc[mask, ycol] = pd.NA
        logging.info(f"    Removed {removed_count} outlier frames for '{part}'")

    # Ensure output directory exists
    os.makedirs(Path(outfile).parent or '.', exist_ok=True)
    logging.info(f"Saving cleaned data to {outfile}")
    df.to_csv(outfile, index=False)


def main():
    parser = argparse.ArgumentParser(
        description="Filter DLC data by positional change (fixed or robust methods)"
    )
    group_inputs = parser.add_mutually_exclusive_group(required=True)
    group_inputs.add_argument('--input', help="Single input CSV file")
    group_inputs.add_argument('--input-dir', help="Directory of CSV files to filter")

    parser.add_argument('--output', help="Single output CSV file path")
    parser.add_argument('--output-dir', help="Directory to save batch output CSVs")

    parser.add_argument(
        '--method', choices=['euclidean', 'x', 'y'], required=True,
        help="Difference metric: euclidean, x, or y"
    )

    # Outlier detection mode: threshold vs. robust vs. percentile
    group_detection = parser.add_mutually_exclusive_group(required=True)
    group_detection.add_argument(
        '--threshold', type=float,
        help="Fixed threshold for positional change (raw units)"
    )
    group_detection.add_argument(
        '--stat-method', choices=['mad', 'iqr', 'adj_iqr', 'std'],
        help="Robust outlier detection: 'mad', 'iqr', 'adj_iqr', or 'std'"
    )
    group_detection.add_argument(
        '--percentile', type=float,
        help="Percentile trimming: remove values above this percentile (0–100)"
    )

    # Robust-mode parameters
    parser.add_argument(
        '--mad-threshold', type=float, default=3.5,
        help="Modified-Z cutoff if using --stat-method mad (default 3.5)"
    )
    parser.add_argument(
        '--iqr-multiplier', type=float, default=1.5,
        help="IQR multiplier if using --stat-method iqr or adj_iqr (default 1.5)"
    )
    parser.add_argument(
        '--std-threshold', type=float, default=3.0,
        help="Z-score cutoff if using --stat-method std (default 3.0)"
    )

    # Optional log-transform
    parser.add_argument(
        '--log-transform', action='store_true',
        help="Apply log(diffs + δ) before robust outlier detection (δ=1e-8)"
    )

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Determine mode and validate parameters
    if args.threshold is not None:
        mode = 'threshold'
    elif args.percentile is not None:
        mode = 'percentile'
    else:
        mode = args.stat_method

    # Single-file vs. batch
    if args.input:
        if not args.output:
            parser.error("--output is required when using --input")
        position_filter(
            infile=args.input,
            outfile=args.output,
            method=args.method,
            mode=mode,
            threshold=args.threshold,
            mad_threshold=args.mad_threshold,
            iqr_multiplier=args.iqr_multiplier,
            std_threshold=args.std_threshold,
            percentile=args.percentile,
            log_transform=args.log_transform
        )
    else:
        if not args.output_dir:
            parser.error("--output-dir is required when using --input-dir")
        os.makedirs(args.output_dir, exist_ok=True)
        pattern = os.path.join(args.input_dir, "*.csv")
        files = glob.glob(pattern)
        logging.info(f"Found {len(files)} CSV(s) in {args.input_dir}")
        for infile in sorted(files):
            outfile = os.path.join(args.output_dir, Path(infile).name)
            position_filter(
                infile=infile,
                outfile=outfile,
                method=args.method,
                mode=mode,
                threshold=args.threshold,
                mad_threshold=args.mad_threshold,
                iqr_multiplier=args.iqr_multiplier,
                std_threshold=args.std_threshold,
                percentile=args.percentile,
                log_transform=args.log_transform
            )


if __name__ == "__main__":
    main()
