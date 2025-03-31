#!/usr/bin/env python3
"""
clean_coordinates.py

Cleans DeepLabCut coordinate data by:
- Inverting y-coordinates (to transform the image-based coordinate system)
- Removing rows with all zero values (indicative of corrupted frames)
- Excluding specified irrelevant body parts

Usage:
    python clean_coordinates.py --input raw_data.csv --output cleaned_data.csv --exclude "handler_leg1,handler_leg2"
"""

import argparse
import logging
import pandas as pd

def clean_coordinates(input_file, output_file, exclude_parts):
    logging.info("Loading data from %s", input_file)
    try:
        data = pd.read_csv(input_file)
    except Exception as e:
        logging.error("Failed to load input file: %s", e)
        raise

    # Invert y-coordinates (assuming columns end with '_y')
    y_columns = [col for col in data.columns if col.endswith('_y')]
    for col in y_columns:
        logging.info("Inverting y-coordinates in column %s", col)
        max_y = data[col].max()
        data[col] = max_y - data[col]

    # Remove rows where all coordinate values are zero
    coord_columns = [col for col in data.columns if '_' in col]
    initial_count = len(data)
    data = data.loc[~(data[coord_columns] == 0).all(axis=1)]
    logging.info("Removed %d zero-value rows", initial_count - len(data))

    # Exclude irrelevant body parts
    if exclude_parts:
        exclude_list = [part.strip() for part in exclude_parts.split(',')]
        logging.info("Excluding body parts: %s", exclude_list)
        for part in exclude_list:
            cols_to_drop = [col for col in data.columns if col.startswith(part)]
            if cols_to_drop:
                data = data.drop(columns=cols_to_drop, errors='ignore')
                logging.info("Dropped columns: %s", cols_to_drop)
    
    logging.info("Saving cleaned data to %s", output_file)
    data.to_csv(output_file, index=False)
    logging.info("Data cleaning completed.")

def main():
    parser = argparse.ArgumentParser(description="Clean DeepLabCut coordinate data.")
    parser.add_argument('--input', required=True, help="Path to input CSV file with raw coordinates.")
    parser.add_argument('--output', required=True, help="Path to output CSV file for cleaned data.")
    parser.add_argument('--exclude', help="Comma-separated list of body parts to exclude.", default="")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    clean_coordinates(args.input, args.output, args.exclude)

if __name__ == "__main__":
    main()
