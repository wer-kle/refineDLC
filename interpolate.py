import pandas as pd
import numpy as np
import os
import glob
import sys

def get_input_directory():
    while True:
        input_dir = input("Enter the path to the input directory containing DeepLabCut CSV files: ").strip('"').strip("'")
        if os.path.isdir(input_dir):
            return input_dir
        else:
            print("Directory not found. Please enter a valid directory path.")

def get_output_directory():
    while True:
        output_dir = input("Enter the path for the output directory to save interpolated CSV files: ").strip('"').strip("'")
        if os.path.isdir(output_dir):
            return output_dir
        else:
            try:
                os.makedirs(output_dir)
                print(f"Output directory '{output_dir}' created.")
                return output_dir
            except Exception as e:
                print(f"Could not create directory '{output_dir}'. Error: {e}")

def select_interpolation_method():
    methods = [
        'linear',
        'time',
        'nearest',
        'zero',
        'slinear',
        'quadratic',
        'cubic',
        'polynomial'
    ]
    print("\nSelect global interpolation method from the following options:")
    for idx, method in enumerate(methods, 1):
        print(f"{idx}. {method}")
    while True:
        choice = input("Enter the number corresponding to the desired interpolation method: ")
        if choice.isdigit() and 1 <= int(choice) <= len(methods):
            method = methods[int(choice)-1]
            break
        else:
            print(f"Please enter a number between 1 and {len(methods)}.")
    degree = None
    if method == 'polynomial':
        while True:
            degree_input = input("Enter the degree of the polynomial for interpolation (integer >0): ")
            if degree_input.isdigit() and int(degree_input) > 0:
                degree = int(degree_input)
                break
            else:
                print("Please enter a valid positive integer for the degree.")
    return method, degree

def get_max_consecutive_missing():
    while True:
        max_missing = input("Enter the maximum number of consecutive missing frames to interpolate (integer >=1): ")
        if max_missing.isdigit() and int(max_missing) >= 1:
            return int(max_missing)
        else:
            print("Please enter a valid integer greater than or equal to 1.")

def select_interpolation_method_for_bodypart(bp):
    methods = [
        'linear',
        'time',
        'nearest',
        'zero',
        'slinear',
        'quadratic',
        'cubic',
        'polynomial'
    ]
    print(f"\nSelect interpolation method for body part '{bp}' from the following options:")
    for idx, method in enumerate(methods, 1):
        print(f"{idx}. {method}")
    while True:
        choice = input("Enter the number corresponding to the desired interpolation method: ")
        if choice.isdigit() and 1 <= int(choice) <= len(methods):
            method = methods[int(choice)-1]
            break
        else:
            print(f"Please enter a number between 1 and {len(methods)}.")
    degree = None
    if method == 'polynomial':
        while True:
            degree_input = input(f"Enter the degree of the polynomial for body part '{bp}' (integer >0): ")
            if degree_input.isdigit() and int(degree_input) > 0:
                degree = int(degree_input)
                break
            else:
                print("Please enter a valid positive integer for the degree.")
    return method, degree

def get_max_consecutive_missing_for_bodypart(bp):
    while True:
        max_missing = input(f"Enter the maximum number of consecutive missing frames to interpolate for body part '{bp}' (integer >=1): ")
        if max_missing.isdigit() and int(max_missing) >= 1:
            return int(max_missing)
        else:
            print("Please enter a valid integer greater than or equal to 1.")

def extract_bodypart_from_column(column):
    """
    Given a column label, return the body part name.
    For DeepLabCut CSVs with three header rows, the columns are MultiIndex tuples:
      (scorer, bodypart, coordinate)
    We extract the body part from the second element if the third element is one of 'x', 'y', or 'likelihood'.
    """
    if isinstance(column, tuple) and len(column) == 3:
        if column[1].lower() == 'frames':
            return None
        if column[2] in ['x', 'y', 'likelihood']:
            return column[1]
    else:
        parts = column.rsplit('_', 1)
        if len(parts) == 2 and parts[1] in ['x', 'y', 'likelihood']:
            return parts[0]
    return None

def get_bodyparts_from_dataframe(df):
    bodyparts = set()
    for col in df.columns:
        bp = extract_bodypart_from_column(col)
        if bp is not None:
            bodyparts.add(bp)
    return sorted(list(bodyparts))

def suggest_global_method(df):
    ratios = []
    for col in df.columns:
        if isinstance(col, tuple) and col[2] in ['x', 'y']:
            series = df[col].dropna()
            if len(series) < 3:
                continue
            first_diff = series.diff().dropna()
            second_diff = first_diff.diff().dropna()
            if first_diff.std() > 0:
                ratios.append(second_diff.std() / first_diff.std())
    if not ratios:
        return "linear"
    avg_ratio = np.mean(ratios)
    return "linear" if avg_ratio < 0.2 else "cubic"

def suggest_method_for_bodypart(df, bp):
    ratios = []
    for col in df.columns:
        if isinstance(col, tuple) and col[1] == bp and col[2] in ['x', 'y']:
            series = df[col].dropna()
            if len(series) < 3:
                continue
            first_diff = series.diff().dropna()
            second_diff = first_diff.diff().dropna()
            if first_diff.std() > 0:
                ratios.append(second_diff.std() / first_diff.std())
    if not ratios:
        return "linear"
    avg_ratio = np.mean(ratios)
    return "linear" if avg_ratio < 0.2 else "cubic"

def get_bodypart_settings(df, bodyparts):
    settings = {}
    for bp in bodyparts:
        recommended = suggest_method_for_bodypart(df, bp)
        prompt = f"For body part '{bp}', the recommended interpolation method is '{recommended}'. Use this recommendation? (Y/n): "
        use_recommended = input(prompt).strip().lower()
        if use_recommended == '' or use_recommended.startswith('y'):
            method, degree = recommended, None
        else:
            method, degree = select_interpolation_method_for_bodypart(bp)
        max_missing = get_max_consecutive_missing_for_bodypart(bp)
        settings[bp] = (method, degree, max_missing)
    return settings

def interpolate_series(series, method, degree, limit):
    try:
        if method == 'polynomial':
            interpolated = series.interpolate(method=method, order=degree, limit=limit, limit_direction='both')
        elif method == 'cubic':
            # Use spline interpolation with order 3 for cubic behavior.
            interpolated = series.interpolate(method='spline', order=3, limit=limit, limit_direction='both')
        else:
            interpolated = series.interpolate(method=method, limit=limit, limit_direction='both')
    except Exception as e:
        print(f"Error interpolating column '{series.name}' with method '{method}': {e}")
        interpolated = series
    return interpolated

def interpolate_dataframe(df, bodypart_settings, default_settings):
    interpolated_df = df.copy()
    for column in interpolated_df.columns:
        series = interpolated_df[column]
        if pd.api.types.is_numeric_dtype(series):
            bp = extract_bodypart_from_column(column)
            if bp and bp in bodypart_settings:
                method, degree, limit = bodypart_settings[bp]
            elif default_settings is not None:
                method, degree, limit = default_settings
            else:
                print(f"No interpolation settings for column '{column}'; skipping interpolation.")
                continue
            interpolated_df[column] = interpolate_series(series, method, degree, limit)
    return interpolated_df

def compute_missing_by_bodypart(df):
    missing_dict = {}
    for col in df.columns:
        bp = extract_bodypart_from_column(col)
        if bp is not None:
            count = df[col].isnull().sum()
            missing_dict[bp] = missing_dict.get(bp, 0) + count
    return missing_dict

def process_file(file_path, output_dir, bodypart_settings, default_settings):
    filename = os.path.basename(file_path)
    output_path = os.path.join(output_dir, filename)
    print(f"\nProcessing file: {filename}")
    try:
        df = pd.read_csv(file_path, header=[0,1,2], index_col=0, na_values=['', 'NA', 'null', '-999', '-1'])
        # Convert index to numeric and sort it.
        df.index = pd.to_numeric(df.index, errors='coerce')
        df.sort_index(inplace=True)
        for col in df.columns:
            if pd.api.types.is_object_dtype(df[col]):
                df[col] = pd.to_numeric(df[col], errors='coerce')
    except Exception as e:
        print(f"Error reading the file '{filename}': {e}")
        return None

    global_missing_before = df.isnull().sum().sum()
    bp_missing_before = compute_missing_by_bodypart(df)
    print(f"Global missing values before interpolation: {global_missing_before}")

    interpolated_df = interpolate_dataframe(df, bodypart_settings, default_settings)
    
    global_missing_after = interpolated_df.isnull().sum().sum()
    bp_missing_after = compute_missing_by_bodypart(interpolated_df)
    print(f"Global missing values after interpolation: {global_missing_after}")
    
    try:
        interpolated_df.to_csv(output_path, index=True)
        print(f"Interpolated data saved to '{output_path}'")
    except Exception as e:
        print(f"Error saving the file '{output_path}': {e}")
    
    return {
        "filename": filename,
        "global_before": global_missing_before,
        "global_after": global_missing_after,
        "bp_before": bp_missing_before,
        "bp_after": bp_missing_after
    }

def write_summary(summary_data, output_dir):
    summary_file = os.path.join(output_dir, "summary.txt")
    lines = []
    lines.append("GLOBAL MISSING VALUES SUMMARY")
    header_global = f"{'File':<30} {'Missing Before':>15} {'Missing After':>15}"
    lines.append(header_global)
    lines.append("-" * len(header_global))
    for data in summary_data:
        lines.append(f"{data['filename']:<30} {data['global_before']:>15} {data['global_after']:>15}")
    
    lines.append("\nPER BODY PART MISSING VALUES SUMMARY")
    header_bp = f"{'File':<30} {'Body Part':<15} {'Missing Before':>15} {'Missing After':>15}"
    lines.append(header_bp)
    lines.append("-" * len(header_bp))
    for data in summary_data:
        filename = data["filename"]
        bp_keys = set(data["bp_before"].keys()) | set(data["bp_after"].keys())
        for bp in sorted(bp_keys):
            before = data["bp_before"].get(bp, 0)
            after = data["bp_after"].get(bp, 0)
            lines.append(f"{filename:<30} {bp:<15} {before:>15} {after:>15}")
    summary_text = "\n".join(lines)
    
    try:
        with open(summary_file, "w") as f:
            f.write(summary_text)
        print(f"\nSummary file saved to '{summary_file}'")
    except Exception as e:
        print(f"Error writing summary file '{summary_file}': {e}")

def main():
    print("DeepLabCut Coordinates Interpolation Script")
    print("-------------------------------------------\n")
    
    input_dir = get_input_directory()
    output_dir = get_output_directory()
    
    print("\nSearching for CSV files in the input directory...")
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    if not csv_files:
        print("No CSV files found in the specified input directory.")
        sys.exit(1)
    
    print(f"Found {len(csv_files)} CSV file(s) to process.")
    
    try:
        df_first = pd.read_csv(csv_files[0], header=[0,1,2], index_col=0, na_values=['', 'NA', 'null', '-999', '-1'])
    except Exception as e:
        print(f"Error reading the first CSV file: {e}")
        df_first = None

    if df_first is not None:
        bodyparts = get_bodyparts_from_dataframe(df_first)
        if bodyparts:
            print("\nDetected the following body parts: " + ", ".join(bodyparts))
            choice = input("Would you like to specify interpolation settings for each body part individually? (y/n): ").strip().lower()
            if choice.startswith('y'):
                bodypart_settings = get_bodypart_settings(df_first, bodyparts)
                default_settings = None
            else:
                recommended = suggest_global_method(df_first)
                use_recommended = input(f"Based on coordinate changes, the recommended global interpolation method is '{recommended}'. Would you like to use it? (Y/n): ").strip().lower()
                if use_recommended == '' or use_recommended.startswith('y'):
                    print(f"Using recommended global method: {recommended}")
                    global_method, global_degree = recommended, None
                else:
                    global_method, global_degree = select_interpolation_method()
                global_max_missing = get_max_consecutive_missing()
                bodypart_settings = {}
                default_settings = (global_method, global_degree, global_max_missing)
        else:
            print("No body parts detected based on header information. Using global interpolation settings.")
            global_method, global_degree = select_interpolation_method()
            global_max_missing = get_max_consecutive_missing()
            bodypart_settings = {}
            default_settings = (global_method, global_degree, global_max_missing)
    else:
        global_method, global_degree = select_interpolation_method()
        global_max_missing = get_max_consecutive_missing()
        bodypart_settings = {}
        default_settings = (global_method, global_degree, global_max_missing)
    
    summary_data = []
    for file_path in csv_files:
        data = process_file(file_path, output_dir, bodypart_settings, default_settings)
        if data is not None:
            summary_data.append(data)
    
    write_summary(summary_data, output_dir)
    print("\nAll files have been processed.")

if __name__ == "__main__":
    main()
