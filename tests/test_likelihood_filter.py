import pandas as pd
import pytest
from pathlib import Path
from refinedlc.likelihood_filter import likelihood_filter

def test_likelihood_filter(tmp_path: Path):
    # Create sample data with one likelihood column and corresponding coordinate columns.
    df = pd.DataFrame({
        "body_likelihood": [0.8, 0.5, 0.7],
        "body_x": [10, 15, 30],
        "body_y": [20, 25, 40]
    })
    
    # Write the sample data to a temporary CSV file.
    input_file = tmp_path / "input.csv"
    df.to_csv(input_file, index=False)
    
    # Define the output CSV file.
    output_file = tmp_path / "output.csv"
    
    # Set the likelihood threshold.
    threshold = 0.6

    # Execute the likelihood_filter function.
    likelihood_filter(str(input_file), str(output_file), threshold)

    # Read the resulting CSV.
    result_df = pd.read_csv(output_file)

    # Expected result:
    # Row with index 1 should have likelihood below threshold, so its likelihood, body_x, and body_y become NaN.
    expected_df = pd.DataFrame({
        "body_likelihood": [0.8, None, 0.7],
        "body_x": [10, None, 30],
        "body_y": [20, None, 40]
    })
    
    pd.testing.assert_frame_equal(result_df, expected_df, check_dtype=False)

def test_no_likelihood_columns(tmp_path: Path):
    # Create sample data without any likelihood columns.
    df = pd.DataFrame({
        "body_x": [10, 15, 30],
        "body_y": [20, 25, 40]
    })
    
    # Write the sample data to a temporary CSV file.
    input_file = tmp_path / "input_no_likelihood.csv"
    df.to_csv(input_file, index=False)
    
    # Define the output CSV file.
    output_file = tmp_path / "output_no_likelihood.csv"
    
    # Use any threshold since there are no likelihood columns.
    threshold = 0.6

    # Execute the likelihood_filter function.
    likelihood_filter(str(input_file), str(output_file), threshold)

    # Read the output data.
    result_df = pd.read_csv(output_file)
    
    # The data should remain unchanged.
    pd.testing.assert_frame_equal(result_df, df, check_dtype=False)
