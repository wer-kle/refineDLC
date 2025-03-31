#!/usr/bin/env python3
"""
position_filter.py

Filters DeepLabCut data based on positional changes between consecutive frames.
If the change in position for a body part exceeds a user-defined threshold, the coordinates are set to NaN.

Usage:
    python position_filter.py --input likelihood_filtered.csv --output position_filtered.csv --method euclidean --threshold 30
"""

import argparse
import logging
import pandas as pd
import numpy as np

def position_filter(input_file, output_file, method, threshold):
    logging.info("Loading data from %s", input_file)
    try:
        data = pd.read_csv(input_file)
    except Exception as e:
        logging.error("Failed to load input file: %s", e)
        raise
    
    # Identify unique body parts based on coordinate column naming convention
    body_parts = set(col.rsplit('_', 1)[0] for col in data.columns if col.endswith('_x'))
    for part in body_parts:
        x_col = part + '_x'
        y_col = part + '_y'
        if x_col not in data.columns or y_col not in data.columns:
            continue
        
        logging.info("Filtering positional changes for body part: %s", part)
        x = data[x_col].to_numpy()
        y = data[y_col].to_numpy()
        # Calculate differences between consecutive frames
        if method == 'euclidean':
            diff = np.sqrt(np.diff(x)**2 + np.diff(y)**2)
        elif method == 'x':
            diff = np.abs(np.diff(x))
        elif method == 'y':
            diff = np.abs(np.diff(y))
        else:
            logging.error("Invalid method: %s. Use 'euclidean', 'x', or 'y'.", method)
            raise ValueError("Invalid method")
        
        # Align differences with the original data (first frame diff set to 0)
        diff = np.insert(diff, 0, 0)
        indices_to_nan = diff > threshold
        data.loc[indices_to_nan, x_col] = None
        data.loc[indices_to_nan, y_col] = None
        logging.info("For body part %s, filtered %d frames based on positional change.", part, indices_to_nan.sum())
    
    logging.info("Saving position-filtered data to %s", output_file)
    data.to_csv(output_file, index=False)
    logging.info("Position filtering completed.")

def main():
    parser = argparse.ArgumentParser(description="Filter DeepLabCut data based on positional changes between consecutive frames.")
    parser.add_argument('--input', required=True, help="Path to input CSV file with likelihood-filtered data.")
    parser.add_argument('--output', required=True, help="Path to output CSV file for position-filtered data.")
    parser.add_argument('--method', choices=['euclidean', 'x', 'y'], required=True, help="Filtering method: 'euclidean', 'x', or 'y'.")
    parser.add_argument('--threshold', type=float, required=True, help="Threshold for positional change (in pixels).")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    position_filter(args.input, args.output, args.method, args.threshold)

if __name__ == "__main__":
    main()
