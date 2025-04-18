# refineDLC: Advanced Post-Processing Pipeline for DeepLabCut Outputs

## Overview
**RefineDLC** is a comprehensive, modular, and user-friendly pipeline designed to process raw DeepLabCut coordinate outputs. The pipeline cleans, filters, and interpolates the data to remove noise and false positives, delivering datasets that are ready for kinematic analysis.

The package comprises four main scripts:
- **clean_coordinates.py**: Inverts y-coordinates, removes zero-value rows, excludes specified body parts, and supports single-file or batch-directory processing.
- **likelihood_filter.py**: Filters out data points with low likelihood scores.
- **position_filter.py**: Removes frames exhibiting physiologically improbable positional changes.
- **interpolate.py**: Interpolates missing data points using a variety of methods.

## Features
- **Modular Design:** Each processing step is implemented as a standalone script.
- **Batch & Single-File Modes:** `clean_coordinates.py` can process one CSV or an entire directory of CSVs in one run.
- **Command-Line Interface:** Each script accepts well-documented command-line arguments.
- **Logging & Error Handling:** Progress is logged and common errors are handled gracefully.
- **Flexible Filtering:** Adjustable thresholds and methods allow the pipeline to be tailored to your dataset.
- **Multiple Interpolation Options:** Choose from several interpolation techniques depending on your needs.

## Installation
Ensure you have Python 3.10 or higher installed. It is recommended to use a virtual environment.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/wer-kle/refineDLC.git
   cd refineDLC
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **(Optional) Install the package:**
   ```bash
   pip install -e .
   ```

## Requirements
- `Python 3.10+`
- `pandas`
- `numpy`
- `scipy`
- `matplotlib` (optional for visualization)

## Usage

### 1. Clean Coordinates

Clean raw DeepLabCut coordinate data by inverting y-coordinates, removing zero rows, and excluding body parts.

**Single-File Mode**
```bash
python refineDLC/clean_coordinates.py \
  --input path/to/raw_coordinates.csv \
  --output path/to/cleaned_coordinates.csv \
  --exclude "bodypart1,bodypart2"
```

**Batch-Directory Mode**
```bash
python refineDLC/clean_coordinates.py \
  --input-dir path/to/raw_csvs/ \
  --output-dir path/to/cleaned_csvs/ \
  --exclude "bodypart1,bodypart2"
```

**Arguments:**
- `--input` / `--input-dir`: Path to a single CSV file or directory of CSV files.
- `--output` / `--output-dir`: Path for the cleaned CSV or directory to save cleaned CSVs.
- `--exclude`: (Optional) Comma-separated list of body parts to drop.

### 2. Likelihood Filtering

Filter data based on likelihood scores.

```bash
python refineDLC/likelihood_filter.py \
  --input path/to/cleaned_coordinates.csv \
  --output path/to/likelihood_filtered.csv \
  --threshold 0.6
```

### 3. Position Filtering

Remove physiologically improbable positional changes.

```bash
python refineDLC/position_filter.py \
  --input path/to/likelihood_filtered.csv \
  --output path/to/position_filtered.csv \
  --method euclidean \
  --threshold 30
```

### 4. Interpolation

Interpolate missing data points after filtering.

```bash
python refineDLC/interpolate.py \
  --input path/to/position_filtered.csv \
  --output path/to/interpolated_data.csv \
  --method cubic \
  --max_gap 5
```

## Example Workflow

```bash
python refineDLC/clean_coordinates.py --input raw_data.csv --output cleaned_data.csv --exclude "bodypart1,bodypart2"
python refineDLC/likelihood_filter.py --input cleaned_data.csv --output likelihood_filtered.csv --threshold 0.6
python refineDLC/position_filter.py --input likelihood_filtered.csv --output position_filtered.csv --method euclidean --threshold 30
python refineDLC/interpolate.py --input position_filtered.csv --output final_data.csv --method cubic --max_gap 5
```

## Structure

```text
refineDLC/
├── README.md
├── setup.py
├── requirements.txt
├── LICENSE
├── .gitignore
├── refineDLC/
│   ├── __init__.py
│   ├── clean_coordinates.py
│   ├── likelihood_filter.py
│   ├── position_filter.py
│   └── interpolate.py
└── tests/
    ├── test_clean_coordinates.py
    ├── test_likelihood_filter.py
    ├── test_position_filter.py
    └── test_interpolate.py
```

