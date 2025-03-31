import os
import sys
import glob
import pandas as pd
import numpy as np

def filter_outliers(dlc_df, threshold=None, percentage=None, per_bodypart=False, metric='euclidean'):
    """
    Given a DLC DataFrame (multi-index columns), filter out outlier coordinates.
    
    There are three filtering metrics available:
      - 'euclidean': filter based on the Euclidean distance between consecutive frames.
      - 'x': filter based solely on the absolute difference in the x-coordinate.
      - 'y': filter based solely on the absolute difference in the y-coordinate.
    
    For each metric, two modes of filtering are available:
      1) Absolute threshold filtering: set coordinates to NaN if the distance/change
         between consecutive frames exceeds 'threshold'.
      2) Percentage filtering: set coordinates to NaN for the set percentage of highest
         distances/changes. This can be applied globally (across all bodyparts) or per bodypart.
    
    Parameters
    ----------
    dlc_df : pd.DataFrame
        The DLC data in multi-index format: (scorer, bodypart, x/y)
    threshold : float, optional
        The maximum allowed distance/change between consecutive frames.
    percentage : float, optional
        The percentage (0 < percentage < 100) of highest distances/changes to filter.
    per_bodypart : bool, optional
        If True, percentage filtering is computed separately for each bodypart.
        If False and percentage is provided, a single global cutoff is used.
    metric : {'euclidean', 'x', 'y'}, optional
        The metric to use for filtering.
        'euclidean' computes sqrt(diff(x)^2 + diff(y)^2),
        'x' computes abs(diff(x)),
        'y' computes abs(diff(y)).
    
    Returns
    -------
    pd.DataFrame
        A DataFrame with outlier coordinates replaced with NaN.
    
    Raises
    ------
    ValueError
        If neither threshold nor percentage is provided, or if an invalid metric is specified.
    """
    filtered_df = dlc_df.copy()

    all_scorers = dlc_df.columns.levels[0]
    all_bodyparts = dlc_df.columns.levels[1]

    # Function to compute the difference array based on the chosen metric.
    def compute_diff(x_vals, y_vals, metric):
        if metric == 'euclidean':
            return np.sqrt(np.diff(x_vals) ** 2 + np.diff(y_vals) ** 2)
        elif metric == 'x':
            return np.abs(np.diff(x_vals))
        elif metric == 'y':
            return np.abs(np.diff(y_vals))
        else:
            raise ValueError("Invalid metric specified. Choose from 'euclidean', 'x', or 'y'.")

    # Global percentage filtering.
    if percentage is not None and not per_bodypart:
        all_diffs = []
        diffs_dict = {}
        for scorer in all_scorers:
            for bodypart in all_bodyparts:
                col_x = (scorer, bodypart, 'x')
                col_y = (scorer, bodypart, 'y')
                if col_x not in dlc_df.columns or col_y not in dlc_df.columns:
                    continue

                x_vals = dlc_df[col_x].values
                y_vals = dlc_df[col_y].values
                d = compute_diff(x_vals, y_vals, metric)
                diffs_dict[(scorer, bodypart)] = d
                all_diffs.extend(d.tolist())

        if len(all_diffs) == 0:
            print("Warning: No differences computed for global filtering.")
            return filtered_df

        global_cutoff = np.percentile(all_diffs, 100 - percentage)

        for scorer in all_scorers:
            for bodypart in all_bodyparts:
                col_x = (scorer, bodypart, 'x')
                col_y = (scorer, bodypart, 'y')
                if col_x not in dlc_df.columns or col_y not in dlc_df.columns:
                    continue

                d = diffs_dict.get((scorer, bodypart))
                if d is None:
                    continue

                outlier_indices = np.where(d > global_cutoff)[0]
                for i in outlier_indices:
                    frame_idx = i + 1  # Remove the coordinate(s) for the subsequent frame.
                    if metric == 'euclidean':
                        filtered_df.iloc[frame_idx, filtered_df.columns.get_loc(col_x)] = np.nan
                        filtered_df.iloc[frame_idx, filtered_df.columns.get_loc(col_y)] = np.nan
                    elif metric == 'x':
                        filtered_df.iloc[frame_idx, filtered_df.columns.get_loc(col_x)] = np.nan
                    elif metric == 'y':
                        filtered_df.iloc[frame_idx, filtered_df.columns.get_loc(col_y)] = np.nan
        return filtered_df

    # Percentage filtering per bodypart.
    elif percentage is not None and per_bodypart:
        for scorer in all_scorers:
            for bodypart in all_bodyparts:
                col_x = (scorer, bodypart, 'x')
                col_y = (scorer, bodypart, 'y')
                if col_x not in dlc_df.columns or col_y not in dlc_df.columns:
                    continue

                x_vals = dlc_df[col_x].values
                y_vals = dlc_df[col_y].values
                d = compute_diff(x_vals, y_vals, metric)
                if len(d) == 0:
                    continue

                cutoff = np.percentile(d, 100 - percentage)
                outlier_indices = np.where(d > cutoff)[0]
                for i in outlier_indices:
                    frame_idx = i + 1
                    if metric == 'euclidean':
                        filtered_df.iloc[frame_idx, filtered_df.columns.get_loc(col_x)] = np.nan
                        filtered_df.iloc[frame_idx, filtered_df.columns.get_loc(col_y)] = np.nan
                    elif metric == 'x':
                        filtered_df.iloc[frame_idx, filtered_df.columns.get_loc(col_x)] = np.nan
                    elif metric == 'y':
                        filtered_df.iloc[frame_idx, filtered_df.columns.get_loc(col_y)] = np.nan
        return filtered_df

    # Absolute threshold filtering.
    elif threshold is not None:
        for scorer in all_scorers:
            for bodypart in all_bodyparts:
                col_x = (scorer, bodypart, 'x')
                col_y = (scorer, bodypart, 'y')
                if col_x not in dlc_df.columns or col_y not in dlc_df.columns:
                    continue

                x_vals = dlc_df[col_x].values
                y_vals = dlc_df[col_y].values
                d = compute_diff(x_vals, y_vals, metric)
                outlier_indices = np.where(d > threshold)[0]
                for i in outlier_indices:
                    frame_idx = i + 1
                    if metric == 'euclidean':
                        filtered_df.iloc[frame_idx, filtered_df.columns.get_loc(col_x)] = np.nan
                        filtered_df.iloc[frame_idx, filtered_df.columns.get_loc(col_y)] = np.nan
                    elif metric == 'x':
                        filtered_df.iloc[frame_idx, filtered_df.columns.get_loc(col_x)] = np.nan
                    elif metric == 'y':
                        filtered_df.iloc[frame_idx, filtered_df.columns.get_loc(col_y)] = np.nan
        return filtered_df

    else:
        raise ValueError("Either 'threshold' or 'percentage' must be provided.")

def process_single_csv(input_csv_path, output_csv_path, threshold=None, percentage=None, per_bodypart=False, metric='euclidean'):
    """
    Reads a single DLC CSV file, filters out outliers based on the specified method,
    and writes the updated CSV to output_csv_path.
    """
    dlc_df = pd.read_csv(input_csv_path, header=[0, 1, 2], index_col=0)
    filtered_df = filter_outliers(dlc_df, threshold=threshold, percentage=percentage, per_bodypart=per_bodypart, metric=metric)
    filtered_df.to_csv(output_csv_path)
    print(f"Saved filtered file: {output_csv_path}")

def process_directory(input_dir, output_dir, threshold=None, percentage=None, per_bodypart=False, metric='euclidean'):
    """
    Iterates over all CSV files in 'input_dir', applies the filtering, 
    and saves them under the same filenames in 'output_dir'.
    """
    os.makedirs(output_dir, exist_ok=True)
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    if not csv_files:
        print(f"No CSV files found in {input_dir}")
        return

    for csv_path in csv_files:
        file_name = os.path.basename(csv_path)
        out_path = os.path.join(output_dir, file_name)
        process_single_csv(csv_path, out_path, threshold=threshold, percentage=percentage, per_bodypart=per_bodypart, metric=metric)

def main():
    """
    Interactive script to filter outliers in DLC CSV files.
    
    The script prompts the user for:
      1) The input directory containing CSV files.
      2) The output directory for the filtered CSVs.
      3) The filtering metric: 'euclidean' (full distance), 'x' (x change) or 'y' (y change).
      4) The filtering method:
         - 'absolute' threshold filtering, or
         - 'percentage' based filtering (with an option for global or per bodypart).
    """
    print("=== DLC Outlier Filtering Script ===\n")

    # Prompt for input directory.
    while True:
        input_directory = input("Enter the path to the input directory containing CSV files: ").strip()
        if os.path.isdir(input_directory):
            break
        else:
            print(f"Error: '{input_directory}' is not a valid directory. Please try again.\n")

    # Prompt for output directory.
    while True:
        output_directory = input("Enter the path to the output directory where filtered CSVs will be saved: ").strip()
        if output_directory:
            try:
                os.makedirs(output_directory, exist_ok=True)
                break
            except Exception as e:
                print(f"Error creating directory '{output_directory}': {e}\n")
        else:
            print("Output directory path cannot be empty. Please try again.\n")

    # Prompt for filtering metric.
    while True:
        metric_input = input("Select filtering metric ('euclidean' for full distance, 'x' for x change, 'y' for y change): ").strip().lower()
        if metric_input in ['euclidean', 'x', 'y']:
            metric = metric_input
            break
        else:
            print("Invalid option. Please enter 'euclidean', 'x', or 'y'.\n")

    # Select filtering method.
    while True:
        method = input("Select filtering method - 'absolute' for threshold or 'percentage' for percentage-based filtering: ").strip().lower()
        if method in ['absolute', 'percentage']:
            break
        else:
            print("Invalid option. Please enter 'absolute' or 'percentage'.\n")

    if method == 'absolute':
        # Prompt for absolute threshold.
        while True:
            threshold_input = input("Enter the threshold value for filtering (positive number): ").strip()
            try:
                threshold = float(threshold_input)
                if threshold <= 0:
                    print("Threshold must be a positive number. Please try again.\n")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter a numerical value for the threshold.\n")
        percentage = None
        per_bodypart = False

    elif method == 'percentage':
        # Prompt for percentage value.
        while True:
            percentage_input = input("Enter the percentage of highest differences to filter (0-100, e.g., 10 for 10%): ").strip()
            try:
                percentage = float(percentage_input)
                if not (0 < percentage < 100):
                    print("Percentage must be between 0 and 100 (non-inclusive). Please try again.\n")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter a numerical value for the percentage.\n")
        # Prompt for global or per-bodypart filtering.
        while True:
            mode_input = input("Filter globally or for each bodypart separately? Enter 'global' or 'per': ").strip().lower()
            if mode_input in ['global', 'per']:
                per_bodypart = (mode_input == 'per')
                break
            else:
                print("Invalid option. Please enter 'global' or 'per'.\n")
        threshold = None

    print("\nProcessing...\n")
    process_directory(input_directory, output_directory, threshold=threshold, percentage=percentage, per_bodypart=per_bodypart, metric=metric)
    print("\n=== Processing Complete ===")

if __name__ == "__main__":
    main()