# refineDLC: Advanced Post-Processing Pipeline for DeepLabCut Outputs

## Overview
**RefineDLC** is a comprehensive, modular, and user-friendly pipeline designed to process raw DeepLabCut coordinate outputs. The pipeline cleans, filters, and interpolates the data to remove noise and false positives, delivering datasets that are ready for kinematic analysis.

The package comprises four main scripts:
- **clean_coordinates.py**: Inverts y-coordinates, removes zero-value rows, and excludes irrelevant body parts.
- **likelihood_filter.py**: Filters out data points with low likelihood scores.
- **position_filter.py**: Removes frames exhibiting physiologically improbable positional changes.
- **interpolate.py**: Interpolates missing data points using a variety of methods.

## Features
- **Modular Design:** Each processing step is implemented as a standalone script.
- **Command-Line Interface:** Each script accepts well-documented command-line arguments.
- **Logging & Error Handling:** Progress is logged and common errors are gracefully handled.
- **Flexible Filtering:** Adjustable thresholds and methods allow the pipeline to be tailored to your dataset.
- **Multiple Interpolation Options:** Choose from several interpolation techniques depending on your needs.

## Installation
Ensure you have Python 3.10 or higher installed. It is recommended to use a virtual environment.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/refineDLC.git
   cd refineDLC
   ```

2.	**Install dependencies:**
  ```bash
  pip install -r requirements.txt
  ```

3.	**(Optional) Install the package:**
  ```bash
  pip install -e .
```



## Requirements
- `Python 3.10+`
- `Pandas`
- `NumPy`
- `SciPy`
- `Matplotlib` (optional for visualization)


## Usage

### 1. Clean Coordinates

Clean raw DeepLabCut coordinate data by inverting y-coordinates, removing zero rows, and excluding irrelevant body parts.

```
python refindlc/clean_coordinates.py \
    --input path/to/raw_coordinates.csv \
    --output path/to/cleaned_coordinates.csv \
    --exclude "bodypart1, bodypart2"
```

**Arguments:**
- `--input`: Path to the raw coordinate data file (CSV).
- `--output`: Path to save the cleaned data.
- `--exclude`: (Optional) Comma-separated list of body parts to exclude from the analysis.

### 2. Likelihood Filtering

Filter data based on likelihood scores.

```
python refindlc/likelihood_filter.py \
    --input path/to/cleaned_coordinates.csv \
    --output path/to/likelihood_filtered.csv \
    --threshold 0.6
```

**Arguments:**
- `--input`: Path to the cleaned coordinate file.
- `--output`: Path to save the likelihood-filtered data.
- `--threshold`: Likelihood threshold below which data points are set to NaN.

### 3. Position Filtering

Filter data based on positional changes between consecutive frames.

```
python refindlc/position_filter.py \
    --input path/to/likelihood_filtered.csv \
    --output path/to/position_filtered.csv \
    --method euclidean \
    --threshold 30
```

Arguments:
- `--input`: Path to the likelihood-filtered coordinate file.
- `--output`: Path to save the position-filtered data.
- `--method`: Filtering method (euclidean, x, or y).
- `--threshold`: Maximum allowed positional change between consecutive frames (in pixels).

### 4. Interpolation

Interpolate missing data points after filtering.

```
python refindlc/interpolate.py \
    --input path/to/position_filtered.csv \
    --output path/to/interpolated_data.csv \
    --method cubic \
    --max_gap 5
```

Arguments:
- `--input`: Path to the position-filtered coordinate file.
- `--output`: Path to save the interpolated data.
- `--method`: Interpolation method (choices: linear, nearest, zero, slinear, quadratic, cubic).
- `--max_gap`: Maximum number of consecutive frames to interpolate.

## Example Workflow

A typical workflow might involve sequentially running the four scripts:

` python refinedlc/clean_coordinates.py --input raw_data.csv --output cleaned_data.csv --exclude "bodypart1,bodypart2"` \

` python refindlc/likelihood_filter.py --input cleaned_data.csv --output likelihood_filtered.csv --threshold 0.6 ` \

` python refindlc/position_filter.py --input likelihood_filtered.csv --output position_filtered.csv --method euclidean --threshold 30 ` \

` python refindlc/interpolate.py --input position_filtered.csv --output final_data.csv --method cubic --max_gap 5 ` \


## Contributing

Contributions are welcome! Please submit pull requests, report issues, or suggest improvements via GitHub.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments

This pipeline was developed to enhance the usability of DeepLabCut outputs by providing a standardized, automated post-processing solution. It builds upon recent advances in markerless tracking and kinematic analysis.
