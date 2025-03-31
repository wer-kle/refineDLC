#!/usr/bin/env python3
"""
interpolate.py

Interpolates missing data points in DeepLabCut coordinate data.
Supports various interpolation methods and limits interpolation to gaps no larger than a user-defined maximum.

Usage:
    python interpolate.py --input position_filtered.csv --output interpolated_data.csv --method cubic --max_gap 5
"""

import argparse
import logging
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d

def interpolate_data(input_file, output_file, method, max_gap):
    logging.info("Loading data from %s", input_file)
    try:
        data = pd.read_csv(input_file)
    except Exception as e:
        logging.error("Failed to load input file: %s", e)
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
        
        # Create an interpolation function based on valid indices and values
        interp_func = interp1d(valid.index, valid.values, kind=method, bounds_error=False, fill_value="extrapolate")
        interpolated_values = interp_func(np.arange(len(series)))
        
        # Apply interpolation only for gaps smaller than or equal to max_gap frames
        series_interp = series.copy()
        isnan_array = series.isna().to_numpy()
        i = 0
        while i < len(series):
            if isnan_array[i]:
                start = i
                while i < len(series) and isnan_array[i]:
                    i += 1
                gap_length = i - start
                if gap_length <= max_gap:
                    series_interp[start:i] = interpolated_values[start:i]
                else:
                    logging.info("Gap from index %d to %d (length %d) exceeds max_gap; left as NaN.", start, i-1, gap_length)
            else:
                i += 1
        data_interpolated[col] = series_interp
    
    logging.info("Saving interpolated data to %s", output_file)
    data_interpolated.to_csv(output_file, index=False)
    logging.info("Interpolation completed.")

def main():
    parser = argparse.ArgumentParser(description="Interpolate missing data points in DeepLabCut coordinate data.")
    parser.add_argument('--input', required=True, help="Path to input CSV file with position-filtered data.")
    parser.add_argument('--output', required=True, help="Path to output CSV file for interpolated data.")
    parser.add_argument('--method', choices=['linear', 'nearest', 'zero', 'slinear', 'quadratic', 'cubic'], default='linear', help="Interpolation method (default: linear).")
    parser.add_argument('--max_gap', type=int, default=5, help="Maximum number of consecutive frames to interpolate (default: 5).")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    interpolate_data(args.input, args.output, args.method, args.max_gap)

if __name__ == "__main__":
    main()
