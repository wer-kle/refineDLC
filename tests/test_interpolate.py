import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from refinedlc.interpolate import interpolate_data

def test_interpolate_data_small_gap(tmp_path: Path):
    """
    Test interpolation on a small gap that is within the allowed max_gap.
    In this example, indices 1 and 2 are NaN in both 'body_x' and 'body_y' and should be interpolated.
    """
    # Create a DataFrame with a gap of 2 (which is <= max_gap)
    df = pd.DataFrame({
        'body_x': [10, np.nan, np.nan, 40, 50, 60],
        'body_y': [20, np.nan, np.nan, 80, 90, 100]
    })
    input_file = tmp_path / "input_small_gap.csv"
    df.to_csv(input_file, index=False)
    
    output_file = tmp_path / "output_small_gap.csv"
    # Use linear interpolation; set max_gap to 2 so that the gap is interpolated.
    interpolate_data(str(input_file), str(output_file), method='linear', max_gap=2)
    
    result_df = pd.read_csv(output_file)
    
    # Expected interpolation:
    # For 'body_x': interpolate between 10 (index 0) and 40 (index 3):
    #   index 1: 10 + (1/3)*(40-10) = 20; index 2: 10 + (2/3)*(40-10) = 30.
    # For 'body_y': interpolate between 20 (index 0) and 80 (index 3):
    #   index 1: 20 + (1/3)*60 = 40; index 2: 20 + (2/3)*60 = 60.
    expected_df = pd.DataFrame({
        'body_x': [10, 20, 30, 40, 50, 60],
        'body_y': [20, 40, 60, 80, 90, 100]
    })
    
    pd.testing.assert_frame_equal(result_df, expected_df, check_dtype=False)

def test_interpolate_data_large_gap(tmp_path: Path):
    """
    Test interpolation where the gap exceeds the max_gap threshold.
    In this case, the gap (indices 1 to 4) should remain as NaN.
    """
    df = pd.DataFrame({
        'body_x': [10, np.nan, np.nan, np.nan, np.nan, 60],
        'body_y': [20, np.nan, np.nan, np.nan, np.nan, 80]
    })
    input_file = tmp_path / "input_large_gap.csv"
    df.to_csv(input_file, index=False)
    
    output_file = tmp_path / "output_large_gap.csv"
    # Set max_gap to 3; the gap here is 4 (indices 1-4), so it should not be interpolated.
    interpolate_data(str(input_file), str(output_file), method='linear', max_gap=3)
    
    result_df = pd.read_csv(output_file)
    # Expected: the gap remains unchanged (all NaN).
    expected_df = pd.DataFrame({
        'body_x': [10, np.nan, np.nan, np.nan, np.nan, 60],
        'body_y': [20, np.nan, np.nan, np.nan, np.nan, 80]
    })
    
    pd.testing.assert_frame_equal(result_df, expected_df, check_dtype=False)

def test_interpolate_data_not_enough_points(tmp_path: Path):
    """
    Test the case where a column does not have enough valid data points to perform interpolation.
    In such columns, the values should remain unchanged.
    """
    # 'body_x' has only one valid point; 'body_y' has two valid points (and should be interpolated for its gap).
    df = pd.DataFrame({
        'body_x': [np.nan, 10, np.nan, np.nan],
        'body_y': [20, np.nan, 30, np.nan]
    })
    input_file = tmp_path / "input_not_enough.csv"
    df.to_csv(input_file, index=False)
    
    output_file = tmp_path / "output_not_enough.csv"
    # Set max_gap to 2.
    interpolate_data(str(input_file), str(output_file), method='linear', max_gap=2)
    
    result_df = pd.read_csv(output_file)
    # Expected:
    # For 'body_x': not enough valid points, so remains unchanged.
    # For 'body_y': valid points at indices 0 and 2 yield interpolation at index 1.
    #   For index 1: 20 + (1/2)*(30-20) = 25; index 3 remains NaN (no valid endpoint).
    expected_df = pd.DataFrame({
        'body_x': [np.nan, 10, np.nan, np.nan],
        'body_y': [20, 25, 30, np.nan]
    })
    
    pd.testing.assert_frame_equal(result_df, expected_df, check_dtype=False)
