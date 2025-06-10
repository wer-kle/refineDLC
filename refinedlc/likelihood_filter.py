#!/usr/bin/env python3
"""
likelihood_filter.py

Filters DeepLabCut data based on likelihood scores.
Low likelihood values result in NaNs in coordinate columns; likelihood values are retained.
Supports single-file or batch-directory processing.
Filtering can be based on a fixed threshold (--threshold) or by removing a percentage of lowest values (--percentile).

Added options:
    --summary-csv: Path to output CSV file with summary of thresholds or removal percentages per bodypart for each file.
        - With --percentile: records the computed threshold value per bodypart.
        - With --threshold: records the percentage of frames removed per bodypart.

Usage:
    # Single-file mode, remove lowest 10% with summary
    python likelihood_filter.py \
        --input data.csv \
        --output filtered.csv \
        --percentile 10 \
        --summary-csv summary.csv

    # Batch mode, fixed threshold with summary
    python likelihood_filter.py \
        --input-dir path/in/ \
        --output-dir path/out/ \
        --threshold 0.6 \
        --summary-csv summary.csv
"""
import argparse
import logging
import pandas as pd
import os
import glob
from pathlib import Path
import sys


def likelihood_filter(input_file: str, output_file: str,
                      threshold: float = None,
                      percentile: float = None,
                      summary: list = None):
    """Apply likelihood-based filtering and record summary data if requested."""
    logging.info("Loading data from %s", input_file)
    data = pd.read_csv(input_file)

    likelihood_cols = [col for col in data.columns if col.endswith('_likelihood')]
    if not likelihood_cols:
        logging.warning("No likelihood columns found in %s. Saving unchanged.", input_file)
        data.to_csv(output_file, index=False)
        return

    total_frames = len(data)
    for col in likelihood_cols:
        base = col[:-len('_likelihood')]
        # Determine threshold or percentile threshold value
        if percentile is not None:
            thresh_val = data[col].quantile(percentile / 100.0)
            logging.info("Removing lowest %.2f%% frames on %s (threshold=%.4f)", percentile, col, thresh_val)
            mask = data[col] < thresh_val
            # record threshold value
            if summary is not None:
                summary.append({'file': Path(input_file).name,
                                'bodypart': base,
                                'value': thresh_val})
        else:
            thresh_val = threshold
            logging.info("Applying fixed threshold on %s (threshold=%.4f)", col, thresh_val)
            mask = data[col] < thresh_val
            # record percent removed
            if summary is not None:
                percent_removed = mask.sum() / total_frames * 100
                summary.append({'file': Path(input_file).name,
                                'bodypart': base,
                                'value': percent_removed})

        # Apply filtering: set coords to NaN
        for suffix in ['_x', '_y']:
            coord_col = f"{base}{suffix}"
            if coord_col in data.columns:
                data.loc[mask, coord_col] = pd.NA

    logging.info("Saving filtered data to %s", output_file)
    data.to_csv(output_file, index=False)


def process_file(input_path: str, output_dir: str,
                 threshold: float = None,
                 percentile: float = None,
                 summary: list = None):
    process_file_name = Path(input_path).name
    out_path = Path(output_dir) / process_file_name
    likelihood_filter(str(input_path), str(out_path), threshold=threshold,
                      percentile=percentile, summary=summary)


def main():
    parser = argparse.ArgumentParser(
        description="Filter DeepLabCut data by likelihood in single or batch mode."
    )
    io_group = parser.add_mutually_exclusive_group(required=True)
    io_group.add_argument('--input', help="Single CSV input path.")
    io_group.add_argument('--input-dir', help="Directory of CSVs to process.")
    parser.add_argument('--output', help="Output path for single CSV.")
    parser.add_argument('--output-dir', help="Directory to save batch outputs.")
    parser.add_argument('--summary-csv', help="Path to save summary CSV.")

    filt_group = parser.add_mutually_exclusive_group(required=True)
    filt_group.add_argument('--threshold', type=float,
                            help="Fixed likelihood threshold below which coords are NaN.")
    filt_group.add_argument('--percentile', type=float,
                            help="Lowest N%% percentile to remove per column.")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    summary = [] if args.summary_csv else None

    if args.input:
        if not args.output:
            parser.error('--output is required with --input')
        likelihood_filter(args.input, args.output,
                          threshold=args.threshold,
                          percentile=args.percentile,
                          summary=summary)
    else:
        if not args.output_dir:
            parser.error('--output-dir is required with --input-dir')
        os.makedirs(args.output_dir, exist_ok=True)
        files = glob.glob(os.path.join(args.input_dir, '*.csv'))
        if not files:
            logging.error("No CSV files found in input directory %s.", args.input_dir)
            sys.exit(1)
        for f in files:
            process_file(f, args.output_dir,
                         threshold=args.threshold,
                         percentile=args.percentile,
                         summary=summary)

    # Write summary CSV if requested
    if args.summary_csv:
        if summary:
            df = pd.DataFrame(summary)
            wide = df.pivot(index='file', columns='bodypart', values='value').reset_index()
            wide.to_csv(args.summary_csv, index=False)
            logging.info("Summary CSV saved to %s", args.summary_csv)
        else:
            logging.error(
                "Summary was requested but no likelihood data was collected. "
                "Possible causes: no files processed or no '_likelihood' columns found in any files."
            )
            sys.exit(1)

if __name__ == '__main__':
    main()
