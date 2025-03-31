import os
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

def get_directory(prompt_message):
    while True:
        dir_path = input(prompt_message).strip()
        if not dir_path:
            print("Input cannot be empty. Please enter a valid directory path.")
            continue
        path = Path(dir_path)
        try:
            path.mkdir(parents=True, exist_ok=True)
            return str(path.resolve())
        except Exception as e:
            print(f"Error creating/accessing directory: {e}. Please try again.")

def get_choice(prompt_message, choices):
    choices_str = "/".join(choices)
    while True:
        choice = input(f"{prompt_message} ({choices_str}): ").strip().lower()
        if choice in choices:
            return choice
        else:
            print(f"Invalid input. Please enter one of the following: {choices_str}.")

def get_yes_no(prompt_message):
    while True:
        choice = input(f"{prompt_message} (yes/no): ").strip().lower()
        if choice in ['yes', 'y']:
            return True
        elif choice in ['no', 'n']:
            return False
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")

def identify_possible_names(input_dir):
    possible_names = set()
    for file_name in os.listdir(input_dir):
        if file_name.endswith('.csv'):
            file_path = os.path.join(input_dir, file_name)
            try:
                df = pd.read_csv(file_path, header=None, nrows=2)
                second_row = df.iloc[1, 1:]
                for val in second_row:
                    if isinstance(val, str):
                        possible_names.add(val.strip())
                break  # Use only the first file to get names
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
    return sorted(possible_names)

def get_names_from_list(possible_names):
    print("\nPossible names identified in the second row (excluding 'bodyparts'):")
    for i, name in enumerate(possible_names):
        print(f"{i+1}. {name}")
    print("\nChoose names to remove from the list above.")
    print("Enter the numbers corresponding to the names to remove, separated by commas (e.g., 1,3,5):")
    while True:
        choices_input = input("Your choices: ").strip()
        if not choices_input:
            print("Input cannot be empty. Please enter at least one number.")
            continue
        try:
            choices = [int(num.strip()) for num in choices_input.split(',') if num.strip()]
            selected_names = [possible_names[i-1] for i in choices if 1 <= i <= len(possible_names)]
            if selected_names:
                return selected_names
            else:
                print("No valid numbers entered. Please try again.")
        except ValueError:
            print("Invalid input. Please enter numbers separated by commas.")

def setup_logging(output_dir):
    log_filename = datetime.now().strftime("processing_log_%Y%m%d_%H%M%S.log")
    log_filepath = os.path.join(output_dir, log_filename)
    
    # Remove any existing handlers.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Configure logging for summary output.
    logging.basicConfig(
        filename=log_filepath,
        filemode='w',
        level=logging.INFO,  # Only INFO level and above will be logged.
        format='%(message)s'  # Only log the message.
    )
    
    logging.info(f"Log initialized: {log_filepath}")

def invert_y_coordinates(df):
    y_columns = []
    for col in df.columns:
        cell_value = df.at[2, col]  # Third row (index 2)
        if isinstance(cell_value, str) and 'y' in cell_value.strip().lower():
            y_columns.append(col)

    # Log summary for y inversion.
    if y_columns:
        logging.info(f"Inverted 'y' columns: {y_columns}")
    else:
        logging.info("No 'y' columns found; inversion skipped.")

    for col in y_columns:
        try:
            df.loc[3:, col] = pd.to_numeric(df.loc[3:, col], errors='coerce') * -1
        except Exception as e:
            logging.error(f"Failed to invert 'y' column {col}: {e}")

    return df, y_columns

def process_file(file_path, output_directory, names_to_remove, invert_y, delete_zero_rows, remove_columns):
    base_name = os.path.basename(file_path)
    zero_rows_deleted = 0

    try:
        df = pd.read_csv(file_path, header=None)
        logging.info(f"Read file: {base_name}")
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file_path, header=None, encoding='ISO-8859-1')
            logging.info(f"Read file with ISO-8859-1 encoding: {base_name}")
        except Exception as e:
            logging.error(f"Failed to read file {base_name}: {e}")
            return zero_rows_deleted
    except Exception as e:
        logging.error(f"Failed to read file {base_name}: {e}")
        return zero_rows_deleted

    if invert_y:
        df, _ = invert_y_coordinates(df)
    
    if delete_zero_rows:
        df_numeric = df.apply(pd.to_numeric, errors='coerce')
        if df_numeric.shape[1] > 2:
            is_zero_row = (df_numeric.iloc[:, 2:] == 0).all(axis=1)
        else:
            is_zero_row = pd.Series([False] * len(df_numeric))
        zero_rows_deleted = is_zero_row.sum()
        df = df[~is_zero_row]
        logging.info(f"Deleted {zero_rows_deleted} zero rows in {base_name}")
    
    if remove_columns and names_to_remove:
        columns_to_remove_list = []
        for col in df.columns[1:]:
            cell_value = df.at[1, col]
            if isinstance(cell_value, str) and cell_value.strip() in names_to_remove:
                columns_to_remove_list.append(col)
        if columns_to_remove_list:
            df = df.drop(columns=columns_to_remove_list)
            logging.info(f"Removed columns {columns_to_remove_list} in {base_name}")
        else:
            logging.info(f"No columns to remove in {base_name}")
    
    output_path = os.path.join(output_directory, base_name)
    try:
        df.to_csv(output_path, index=False, header=False)
        logging.info(f"Saved processed file: {base_name}")
    except Exception as e:
        logging.error(f"Failed to save file {base_name}: {e}")

    return zero_rows_deleted

def process_files(input_directory, output_directory, names_to_remove, invert_y, delete_zero_rows, remove_columns):
    csv_files = [f for f in os.listdir(input_directory) if f.endswith('.csv')]
    if not csv_files:
        print("No CSV files found in the input directory.")
        return []

    print("\nProcessing files...")
    report_data = []

    for file_name in tqdm(csv_files, desc="Progress", unit="file"):
        file_path = os.path.join(input_directory, file_name)
        zero_deleted = process_file(file_path, output_directory, names_to_remove, invert_y, delete_zero_rows, remove_columns)
        if delete_zero_rows:
            report_data.append({
                'file_name': file_name,
                'zero_rows_deleted': zero_deleted
            })

    return report_data

def main():
    print("=== CLEAN COORDINATES ===\n")
    input_dir = get_directory("Enter the path to the input directory containing CSV files: ")
    output_dir = get_directory("Enter the path to the output directory where cleaned files will be saved: ")

    setup_logging(output_dir)

    print("\n** Data Cleaning Options **\n")
    invert_y = get_yes_no("Do you want to invert 'y' coordinates?")
    delete_zero_rows = get_yes_no("Do you want to delete zero rows?")
    remove_columns = get_yes_no("Do you want to remove columns containing specified names?")

    if remove_columns:
        print("Identifying bodyparts' names...")
        possible_names = identify_possible_names(input_dir)
        if possible_names:
            names_to_remove = get_names_from_list(possible_names)
            logging.info(f"Names to remove: {', '.join(names_to_remove)}")
        else:
            print("No bodyparts' names identified. Please check your input data!")
            names_to_remove = []
    else:
        names_to_remove = []

    logging.info("Data cleaning options selected:")
    logging.info(f"Invert 'y': {invert_y}, Delete zero rows: {delete_zero_rows}, Remove columns: {remove_columns}")
    if remove_columns and names_to_remove:
        logging.info(f"Names to remove: {', '.join(names_to_remove)}")

    report_data = process_files(input_dir, output_dir, names_to_remove, invert_y, delete_zero_rows, remove_columns)

    if delete_zero_rows and report_data:
        report_df = pd.DataFrame(report_data)
        report_filename = "zero_rows_deleted_report.csv"
        report_path = os.path.join(output_dir, report_filename)
        try:
            report_df.to_csv(report_path, index=False)
            print(f"\nZero rows deleted report saved to: {report_path}")
            logging.info(f"Zero rows deleted report saved to: {report_path}")
        except Exception as e:
            print(f"Failed to save zero rows deleted report: {e}")
            logging.error(f"Failed to save zero rows deleted report: {e}")

    print("\nData cleaning process completed.")
    logging.info("Data cleaning process completed.")

if __name__ == "__main__":
    main()
