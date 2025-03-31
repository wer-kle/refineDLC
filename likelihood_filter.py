#!/usr/bin/env python3
"""
likelihood_filter.py

Filters DeepLabCut data based on likelihood scores.
Low likelihood values (below a given threshold) are set to NaN for both likelihood and associated coordinate columns.

Usage:
    python likelihood_filter.py --input cleaned_data.csv --output likelihood_filtered.csv --threshold 0.6
"""

import argparse
import logging
import pandas as pd

def likelihood_filter(input_file, output_file, threshold):
    logging.info("Loading data from %s", input_file)
    try:
        data = pd.read_csv(input_file)
    except Exception as e:
        logging.error("Failed to load input file: %s", e)
        raise
    
    # Identify likelihood columns (assume naming: <bodypart>_likelihood)
    likelihood_cols = [col for col in data.columns if col.endswith('_likelihood')]
    if not likelihood_cols:
        logging.warning("No likelihood columns found. Exiting filtering.")
        data.to_csv(output_file, index=False)
        return
    
    for col in likelihood_cols:
        logging.info("Filtering column %s with threshold %.2f", col, threshold)
        # Set low-likelihood values to NaN
        data.loc[data[col] < threshold, col] = None
        # Also set the corresponding coordinate columns to NaN
        base = col.replace('_likelihood', '')
        for suffix in ['_x', '_y']:
            coord_col = base + suffix
            if coord_col in data.columns:
                data.loc[data[col].isna(), coord_col] = None

    logging.info("Saving likelihood-filtered data to %s", output_file)
    data.to_csv(output_file, index=False)
    logging.info("Likelihood filtering completed.")

def main():
    parser = argparse.ArgumentParser(description="Filter DeepLabCut data based on likelihood scores.")
    parser.add_argument('--input', required=True, help="Path to input CSV file with cleaned coordinates.")
    parser.add_argument('--output', required=True, help="Path to output CSV file for likelihood-filtered data.")
    parser.add_argument('--threshold', type=float, required=True, help="Likelihood threshold below which data are filtered.")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    likelihood_filter(args.input, args.output, args.threshold)

if __name__ == "__main__":
    main()
