#!/usr/bin/env python3
"""
interpolate.py

Interpolates missing data points in DeepLabCut coordinate data.
Supports various interpolation methods and limits interpolation to gaps no larger than a user-defined maximum.
Supports single-file or batch-directory processing, with diagnostic logging of NaN counts before and after.

Usage:
    # Single-file mode
    python interpolate.py \
        --input position_filtered.csv \
        --output interpolated_data.csv \
        --method cubic \
        --max_gap 5

    # Batch-directory mode
    python interpolate.py \
        --input-dir path/to/position_filtered_csvs/ \
        --output-dir path/to/interpolated_csvs/ \
        --method cubic \
        --max_gap 5
"""

import argparse
import logging
import pandas as pd
import os
import glob
from pathlib import Path


def interpolate_data(input_file: str, output_file: str, method: str, max_gap: int):
    logging.info("=== interpolate_data start for %s ===", input_file)
    try:
        data = pd.read_csv(input_file)
    except Exception as e:
        logging.error("Failed to load input file %s: %s", input_file, e)
        raise

    coord_columns = [col for col in data.columns if col.endswith('_x') or col.endswith('_y')]
    data_interpolated = data.copy()

    # Minimum valid points required per method
    min_points = {
        'nearest': 2,
        'linear': 2,
        'zero': 2,
        'slinear': 2,
        'quadratic': 3,
        'cubic': 4
    }

    for col in coord_columns:
        series = data[col]
        before_nans = series.isna().sum()
        valid = series.dropna()
        logging.info("Column '%s': %d NaNs before interpolation", col, before_nans)

        # Determine if fallback to linear is needed
        use_method = method
        if len(valid) < min_points.get(method, 2):
            logging.warning(
                "Column %s has only %d valid points; falling back to linear interpolation.",
                col, len(valid)
            )
            use_method = 'linear'

        logging.info(
            "Interpolating column %s with method '%s' and max_gap=%d", 
            col, use_method, max_gap
        )

        # Perform interpolation for interior gaps
        interp_series = series.interpolate(
            method=use_method,
            limit=max_gap,
            limit_direction='both'
        )
        # Fill leading/trailing small gaps via backward/forward fill
        interp_series = interp_series.fillna(method='bfill', limit=max_gap)
        interp_series = interp_series.fillna(method='ffill', limit=max_gap)

        after_nans = interp_series.isna().sum()
        logging.info("Column '%s': %d NaNs after interpolation", col, after_nans)

        data_interpolated[col] = interp_series

    logging.info("Saving interpolated data to %s", output_file)
    data_interpolated.to_csv(output_file, index=False)
    logging.info("=== interpolate_data end for %s ===", input_file)


def process_file(input_path: str, output_dir: str, method: str, max_gap: int):
    filename = Path(input_path).name
    output_path = Path(output_dir) / filename
    interpolate_data(str(input_path), str(output_path), method, max_gap)


def main():
    parser = argparse.ArgumentParser(
        description="Interpolate missing data points in DeepLabCut data (single-file or batch) with diagnostics."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--input', help="Path to a single position-filtered CSV file.")
    group.add_argument('--input-dir', help="Directory containing position-filtered CSV files.")

    parser.add_argument('--output', help="Path to save a single output CSV.")
    parser.add_argument('--output-dir', help="Directory to save batch output CSVs.")
    parser.add_argument(
        '--method',
        choices=['linear', 'nearest', 'zero', 'slinear', 'quadratic', 'cubic'],
        default='linear',
        help="Interpolation method (default: linear)."
    )
    parser.add_argument(
        '--max_gap', type=int, default=5,
        help="Maximum consecutive NaNs to fill (default: 5)."
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    if args.input:
        if not args.output:
            parser.error('--output is required when using --input')
        interpolate_data(args.input, args.output, args.method, args.max_gap)
    else:
        if not args.output_dir:
            parser.error('--output-dir is required when using --input-dir')
        os.makedirs(args.output_dir, exist_ok=True)

        pattern = os.path.join(args.input_dir, '*.csv')
        files = glob.glob(pattern)
        logging.info("Found %d CSV files in %s", len(files), args.input_dir)
        for input_path in files:
            logging.info("Processing file %s", input_path)
            process_file(input_path, args.output_dir, args.method, args.max_gap)


if __name__ == "__main__":
    main()
