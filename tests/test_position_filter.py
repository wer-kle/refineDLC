import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from refinedlc.position_filter import position_filter

def test_position_filter_euclidean(tmp_path: Path):
    """
    Test the 'euclidean' method:
    - For a body part 'part1' with coordinates:
        Row0: (10,20)
        Row1: (12,24)  -> Euclidean diff ≈ 4.47 (below threshold 5)
        Row2: (20,30)  -> Euclidean diff = 10 (above threshold 5)
    Expected result:
        Row0 and Row1 remain unchanged,
        Row2 has both coordinates set to NaN.
    """
    df = pd.DataFrame({
        "part1_x": [10, 12, 20],
        "part1_y": [20, 24, 30]
    })
    input_file = tmp_path / "input_euclidean.csv"
    df.to_csv(input_file, index=False)

    output_file = tmp_path / "output_euclidean.csv"
    threshold = 5.0
    method = "euclidean"

    position_filter(str(input_file), str(output_file), method, threshold)

    result_df = pd.read_csv(output_file)
    expected_df = pd.DataFrame({
        "part1_x": [10, 12, np.nan],
        "part1_y": [20, 24, np.nan]
    })
    pd.testing.assert_frame_equal(result_df, expected_df, check_dtype=False)

def test_position_filter_x(tmp_path: Path):
    """
    Test the 'x' method:
    - For a body part 'part1' with coordinates:
        Row0: (10,20)
        Row1: (16,21) -> x-diff = 6 (above threshold 5)
        Row2: (20,22) -> x-diff = 4 (below threshold)
    Expected result:
        Row0 and Row2 remain unchanged,
        Row1 has both coordinates set to NaN.
    """
    df = pd.DataFrame({
        "part1_x": [10, 16, 20],
        "part1_y": [20, 21, 22]
    })
    input_file = tmp_path / "input_x.csv"
    df.to_csv(input_file, index=False)

    output_file = tmp_path / "output_x.csv"
    threshold = 5.0
    method = "x"

    position_filter(str(input_file), str(output_file), method, threshold)

    result_df = pd.read_csv(output_file)
    expected_df = pd.DataFrame({
        "part1_x": [10, np.nan, 20],
        "part1_y": [20, np.nan, 22]
    })
    pd.testing.assert_frame_equal(result_df, expected_df, check_dtype=False)

def test_position_filter_y(tmp_path: Path):
    """
    Test the 'y' method:
    - For a body part 'part1' with coordinates:
        Row0: (10,20)
        Row1: (12,27) -> y-diff = 7 (above threshold 5)
        Row2: (15,35) -> y-diff = 8 (above threshold 5)
    Expected result:
        Row0 remains unchanged,
        Row1 and Row2 have both coordinates set to NaN.
    """
    df = pd.DataFrame({
        "part1_x": [10, 12, 15],
        "part1_y": [20, 27, 35]
    })
    input_file = tmp_path / "input_y.csv"
    df.to_csv(input_file, index=False)

    output_file = tmp_path / "output_y.csv"
    threshold = 5.0
    method = "y"

    position_filter(str(input_file), str(output_file), method, threshold)

    result_df = pd.read_csv(output_file)
    expected_df = pd.DataFrame({
        "part1_x": [10, np.nan, np.nan],
        "part1_y": [20, np.nan, np.nan]
    })
    pd.testing.assert_frame_equal(result_df, expected_df, check_dtype=False)
