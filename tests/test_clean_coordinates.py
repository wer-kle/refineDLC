import pandas as pd
import pytest
from pathlib import Path
from refinedlc.clean_coordinates import clean_coordinates

def test_clean_coordinates(tmp_path: Path):
    # Create sample input data with coordinate columns.
    # Row 1 is all zeros and should be removed.
    sample_data = pd.DataFrame({
        "handler_leg1_x": [10, 0, 5],
        "handler_leg1_y": [20, 0, 15],
        "body_x": [5, 0, 3],
        "body_y": [25, 0, 20]
    })

    # Write the sample data to a temporary input CSV file.
    input_csv = tmp_path / "input.csv"
    sample_data.to_csv(input_csv, index=False)

    # Define the output CSV file path.
    output_csv = tmp_path / "output.csv"

    # Specify body parts to exclude.
    exclude_parts = "handler_leg1"

    # Execute the cleaning function.
    clean_coordinates(str(input_csv), str(output_csv), exclude_parts)

    # Read the cleaned output.
    cleaned_data = pd.read_csv(output_csv)

    # Check that the row with all zeros (row index 1) has been removed.
    # Original data had 3 rows; we expect 2 rows after cleaning.
    assert len(cleaned_data) == 2

    # Verify that columns starting with 'handler_leg1' have been dropped.
    assert "handler_leg1_x" not in cleaned_data.columns
    assert "handler_leg1_y" not in cleaned_data.columns

    # The remaining columns should be 'body_x' and 'body_y'.
    expected_columns = {"body_x", "body_y"}
    assert set(cleaned_data.columns) == expected_columns

    # Verify that the y-coordinate inversion was applied correctly.
    # For column "body_y", the max value in the original sample was 25.
    # The inversion should be: new_value = max_y - original_value.
    # For the remaining rows (original indices 0 and 2):
    #   - Row 0: 25 - 25 = 0
    #   - Row 2: 25 - 20 = 5
    expected_body_y = [0, 5]
    pd.testing.assert_series_equal(
        cleaned_data["body_y"].reset_index(drop=True),
        pd.Series(expected_body_y, name="body_y"),
        check_dtype=False
    )
