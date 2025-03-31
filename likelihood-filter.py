"""
DeepLabCut CSV Filtering Script (Aggregate Filtering Across Files)

This script processes DeepLabCut CSV files (with a three-level header) by first
aggregating likelihood values across all files and then computing filtering thresholds.
The threshold can be defined as:
  1) A percentage of the lowest likelihood values (computed either globally or per-bodypart), or
  2) A fixed numeric threshold.
  
For percentage-based filtering the script outputs the computed likelihood threshold value(s);
for a fixed threshold it outputs the overall percentage of frames discarded per bodypart.
The filter (i.e. removal of x and y coordinates) is then applied using the computed threshold(s).
Filtered CSV files are saved in a user-specified output directory.
"""

import os
import sys
import glob
import numpy as np
import pandas as pd
from tqdm import tqdm  # Make sure to install tqdm (e.g., pip install tqdm)

def aggregate_likelihood(csv_files, mode, selected_bodyparts):
    """
    Aggregate likelihood values across all CSV files.
    
    Parameters:
        csv_files (list): List of CSV file paths.
        mode (str): 'global' or 'per' for filtering mode.
        selected_bodyparts (list): If not empty, only include these bodyparts.
    
    Returns:
        global_likelihood (list): Aggregated likelihood values (if mode is 'global').
        bp_likelihood (dict): Dictionary mapping bodypart to list of likelihood values (if mode is 'per').
    """
    global_likelihood = []
    bp_likelihood = {}
    
    for file in csv_files:
        try:
            df = pd.read_csv(file, header=[0, 1, 2])
        except Exception as e:
            print(f"Error reading {file}: {e}")
            continue
        
        for col in df.columns:
            if col[2].strip().lower() == "likelihood":
                bp = col[1]
                if selected_bodyparts and bp not in selected_bodyparts:
                    continue
                series = pd.to_numeric(df[col], errors='coerce')
                valid_vals = series.dropna().tolist()
                if mode == 'global':
                    global_likelihood.extend(valid_vals)
                elif mode == 'per':
                    bp_likelihood.setdefault(bp, []).extend(valid_vals)
    return global_likelihood, bp_likelihood

def apply_filter_to_file(file_path, mode, thresh_type, thresholds, selected_bodyparts):
    """
    Apply the precomputed threshold(s) to a CSV file.
    
    Parameters:
        file_path (str): Path to the CSV file.
        mode (str): 'global' or 'per'.
        thresh_type (str): 'percentage' or 'fixed'.
        thresholds: For 'global' mode, a single float threshold; for 'per' mode, a dict mapping bp to threshold.
        selected_bodyparts (list): If not empty, only process these bodyparts; otherwise, process all available.
        
    Returns:
        filtered_df (pd.DataFrame): DataFrame with x and y values set to NaN where likelihood is below threshold.
        file_discarded (dict): Discarded frame count per bodypart for this file.
        file_total_frames (dict): Total frame count per bodypart for this file.
    """
    try:
        df = pd.read_csv(file_path, header=[0, 1, 2])
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None, None, None
    
    file_discarded = {}
    file_total_frames = {}
    
    available_bps = {col[1] for col in df.columns if col[2].strip().lower() == "likelihood"}
    if selected_bodyparts:
        bodyparts = [bp for bp in selected_bodyparts if bp in available_bps]
    else:
        bodyparts = list(available_bps)
    
    for bp in bodyparts:
        likelihood_col = None
        for col in df.columns:
            if col[1] == bp and col[2].strip().lower() == "likelihood":
                likelihood_col = col
                break
        if likelihood_col is None:
            continue
        series = pd.to_numeric(df[likelihood_col], errors='coerce')
        total_frames = len(series)
        file_total_frames[bp] = total_frames
        
        if mode == 'global':
            threshold = thresholds
        elif mode == 'per':
            threshold = thresholds.get(bp, None)
            if threshold is None:
                continue
        
        mask = series < threshold
        discarded = int(mask.sum())
        file_discarded[bp] = discarded
        
        for col in df.columns:
            if col[1] == bp and col[2].strip().lower() in ['x', 'y']:
                df.loc[mask, col] = np.nan
                
    return df, file_discarded, file_total_frames

def main():
    print("DeepLabCut Coordinates Likelihood Filter")
    print("---------------------------------------------------------------------")
    
    directory = input("Enter the path to the input directory containing CSV files: ").strip()
    if not os.path.isdir(directory):
        print("Error: The provided directory does not exist.")
        sys.exit(1)
    csv_files = glob.glob(os.path.join(directory, "*.csv"))
    if not csv_files:
        print("Error: No CSV files found in the provided directory.")
        sys.exit(1)
    
    print("\nSelect filtering mode:")
    print("  1: Global filtering (one threshold computed from all selected bodyparts)")
    print("  2: Per-bodypart filtering (each bodypart gets its own threshold)")
    mode_choice = input("Enter 1 or 2: ").strip()
    if mode_choice == "1":
        mode = "global"
    elif mode_choice == "2":
        mode = "per"
    else:
        print("Invalid choice. Exiting.")
        sys.exit(1)
    
    print("\nSelect threshold type:")
    print("  1: Percentage of lowest likelihood values")
    print("  2: Fixed numeric threshold")
    thresh_choice = input("Enter 1 or 2: ").strip()
    if thresh_choice == "1":
        thresh_type = "percentage"
        while True:
            try:
                perc_input = input("Enter the percentage (0-100) of the lowest likelihood values to filter out: ").strip()
                thresh_val = float(perc_input)
                if 0 <= thresh_val <= 100:
                    break
                else:
                    print("Please enter a value between 0 and 100.")
            except ValueError:
                print("Invalid input. Please enter a numeric value.")
    elif thresh_choice == "2":
        thresh_type = "fixed"
        while True:
            try:
                fixed_input = input("Enter the fixed threshold value (e.g., 0.5): ").strip()
                thresh_val = float(fixed_input)
                if 0 <= thresh_val <= 1:
                    break
                else:
                    print("Please enter a value between 0 and 1.")
            except ValueError:
                print("Invalid input. Please enter a numeric value.")
    else:
        print("Invalid threshold type choice. Exiting.")
        sys.exit(1)
    
    specific_bp = input("\nDo you want to apply the filter to the selected bodyparts only? (y/n): ").strip().lower()
    selected_bodyparts = []
    if specific_bp == 'y':
        try:
            df_sample = pd.read_csv(csv_files[0], header=[0, 1, 2])
        except Exception as e:
            print(f"Error reading sample CSV file: {e}")
            sys.exit(1)
        available_bps = []
        for col in df_sample.columns:
            if col[2].strip().lower() == "likelihood":
                bp = col[1]
                if bp not in available_bps:
                    available_bps.append(bp)
        if not available_bps:
            print("No bodyparts found in the likelihood columns of the sample file.")
            sys.exit(1)
        print("\nAvailable bodyparts:")
        for idx, bp in enumerate(available_bps, start=1):
            print(f"  {idx}: {bp}")
        indices_input = input("Enter the numbers of the bodyparts to filter (comma-separated): ").strip()
        try:
            indices = [int(x.strip()) for x in indices_input.split(",") if x.strip().isdigit()]
            for i in indices:
                if 1 <= i <= len(available_bps):
                    selected_bodyparts.append(available_bps[i-1])
                else:
                    print(f"Warning: {i} is out of range and will be ignored.")
        except Exception as e:
            print("Error parsing the bodypart numbers. Exiting.")
            sys.exit(1)
    
    output_dir = input("\nEnter the output directory where filtered CSV files will be saved: ").strip()
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        except Exception as e:
            print(f"Error creating output directory: {e}")
            sys.exit(1)
    
    global_likelihood, bp_likelihood = aggregate_likelihood(csv_files, mode, selected_bodyparts)
    
    if mode == "global":
        if thresh_type == "percentage":
            if not global_likelihood:
                print("No likelihood data found for selected bodyparts across files.")
                sys.exit(1)
            global_thresh = np.percentile(global_likelihood, thresh_val)
            print(f"\nGlobal percentage-based threshold: {global_thresh:.4f}")
            thresholds = global_thresh
        else:
            thresholds = thresh_val
    elif mode == "per":
        thresholds = {}
        if thresh_type == "percentage":
            for bp, values in bp_likelihood.items():
                if values:
                    thresholds[bp] = np.percentile(values, thresh_val)
                else:
                    thresholds[bp] = None
            print("\nPer-bodypart percentage-based thresholds:")
            for bp, t in thresholds.items():
                if t is not None:
                    print(f"  {bp}: {t:.4f}")
                else:
                    print(f"  {bp}: No valid likelihood data")
        else:
            for bp in bp_likelihood.keys():
                thresholds[bp] = thresh_val
    
    overall_discarded = {}
    overall_total = {}
    
    for csv_file in tqdm(csv_files, desc="Processing files", unit="file"):
        filtered_df, file_discarded, file_total_frames = apply_filter_to_file(
            csv_file, mode, thresh_type, thresholds, selected_bodyparts)
        if filtered_df is None:
            continue
        
        for bp, count in file_discarded.items():
            overall_discarded[bp] = overall_discarded.get(bp, 0) + count
        for bp, total in file_total_frames.items():
            overall_total[bp] = overall_total.get(bp, 0) + total
        
        base, ext = os.path.splitext(os.path.basename(csv_file))
        output_path = os.path.join(output_dir, f"{base}_filtered{ext}")
        filtered_df.to_csv(output_path, index=False)
    
    if thresh_type == "fixed":
        print("\nOverall percentage of discarded frames per bodypart:")
        for bp in overall_discarded:
            total = overall_total.get(bp, 0)
            discarded = overall_discarded[bp]
            perc = (discarded / total * 100) if total > 0 else 0
            print(f"  {bp}: {perc:.2f}%")
    else:
        print("\nDiscarded frames (raw count) aggregated across files:")
        for bp in overall_discarded:
            print(f"  {bp}: {overall_discarded[bp]}")
    
if __name__ == '__main__':
    main()
