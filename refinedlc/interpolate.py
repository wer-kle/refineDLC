#!/usr/bin/env python3
"""
interpolate.py

Interpolates missing data points in DeepLabCut coordinate data.
Supports various interpolation methods and limits interpolation to gaps no larger than a user-defined maximum.
Supports single-file or batch-directory processing.

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
import numpy as np
import os
import glob
from pathlib import Path
from scipy.interpolate import interp1d


def interpolate_data(input_file: str, output_file: str, method: str, max_gap: int):
    logging.info("Loading data from %s", input_file)
    try:
        data = pd.read_csv(input_file)
    except Exception as e:
        logging.error("Failed to load input file %s: %s", input_file, e)
        raise

    coord_columns = [col for col in data.columns if col.endswith('_x') or col.endswith('_y')]
    data_interpolated = data.copy()

    for col in coord_columns:
        logging.info("Interpolating column %s using method '%s'", col, method)
        series = data[col]
        isnan = series.isna()
        valid = series[~isnan]
        if len(valid) < 2:
            logging.warning("Not enough data points in column %s to interpolate.", col)
            continue

        interp_func = interp1d(valid.index, valid.values, kind=method,
                               bounds_error=False, fill_value="extrapolate")
        interpolated_values = interp_func(np.arange(len(series)))

        series_interp = series.copy()
        isnan_array = isnan.to_numpy()
        i = 0
        while i < len(series_interp):
            if isnan_array[i]:
                start = i
                while i < len(series_interp) and isnan_array[i]:
                    i += 1
                gap_length = i - start
                if gap_length <= max_gap:
                    series_interp[start:i] = interpolated_values[start:i]
                else:
                    logging.info(
                        "Gap from index %d to %d (length %d) exceeds max_gap; left as NaN.",
                        start, i-1, gap_length
                    )
            else:
                i += 1
        data_interpolated[col] = series_interp

    logging.info("Saving interpolated data to %s", output_file)
    data_interpolated.to_csv(output_file, index=False)
    logging.info("Interpolation completed for %s.", input_file)


def process_file(input_path: str, output_dir: str, method: str, max_gap: int):
    """Helper: apply interpolation to a single CSV and save into the output directory."""
    filename = Path(input_path).name
    output_path = Path(output_dir) / filename
    interpolate_data(str(input_path), str(output_path), method, max_gap)


def main():
    parser = argparse.ArgumentParser(
        description="Interpolate missing data points in DeepLabCut data in single or batch mode."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--input', help="Path to a single position-filtered CSV file.")
    group.add_argument('--input-dir', help="Directory containing position-filtered CSV files.")

    parser.add_argument('--output', help="Path to save single output CSV.")
    parser.add_argument('--output-dir', help="Directory to save batch output CSVs.")
    parser.add_argument(
        '--method',
        choices=['linear', 'nearest', 'zero', 'slinear', 'quadratic', 'cubic'],
        default='linear',
        help="Interpolation method (default: linear)."
    )
    parser.add_argument(
        '--max_gap', type=int, default=5,
        help="Maximum number of consecutive frames to interpolate (default: 5)."
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
        for file_path in files:
            logging.info("Processing file %s", file_path)
            process_file(file_path, args.output_dir, args.method, args.max_gap)


if __name__ == "__main__":
    main()
