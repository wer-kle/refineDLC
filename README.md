# refineDLC: Advanced Post-Processing Pipeline for DeepLabCut Outputs

## Overview
**RefineDLC** is a modular, command-line toolkit that processes raw DeepLabCut coordinate outputs through four standalone Python scripts. Each script supports both single-file and batch-directory modes, enabling scalable pipelines for kinematic data cleaning, filtering, and interpolation.

## Features
- **Modular CLI Tools:** Clean, filter, and interpolate in separate, composable steps.
- **Single-File & Batch Modes:** Glob all `.csv` in a folder or target one file.
- **Logging & Error Handling:** Informative logs at each step, with graceful fallbacks.
- **Flexible Thresholds & Methods:** Adjustable parameters for cleaning, likelihood filtering, movement thresholds, and interpolation methods.
- **Directory Processing:** Automatic directory creation and filename preservation.

## Installation
Requires Python 3.10 or higher. A virtual environment is recommended.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/wer-kle/refineDLC.git
   cd refineDLC
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **(Optional) Install in editable mode:**
   ```bash
   pip install -e .
   ```

## Requirements
- Python 3.10+
- pandas
- numpy
- scipy
- matplotlib (optional)

## Usage
All scripts live in the `refineDLC/` package and can be invoked directly or via `-m refineDLC.<script>`.

### 1. Clean Coordinates
Invert y-coordinates, remove all-zero rows, and exclude unwanted body parts.

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

### 2. Likelihood Filtering
Mask out coordinate values where likelihood falls below a threshold; likelihood columns are retained.

**Single-File Mode**
```bash
python refineDLC/likelihood_filter.py \
  --input path/to/cleaned_coordinates.csv \
  --output path/to/likelihood_filtered.csv \
  --threshold 0.6
```

**Batch-Directory Mode**
```bash
python refineDLC/likelihood_filter.py \
  --input-dir path/to/cleaned_csvs/ \
  --output-dir path/to/likelihood_filtered_csvs/ \
  --threshold 0.6
```

### 3. Position Filtering
Set coordinate cells to NaN when positional change between frames exceeds a pixel threshold.

**Single-File Mode**
```bash
python refineDLC/position_filter.py \
  --input path/to/likelihood_filtered.csv \
  --output path/to/position_filtered.csv \
  --method euclidean \
  --threshold 30
```

**Batch-Directory Mode**
```bash
python refineDLC/position_filter.py \
  --input-dir path/to/likelihood_filtered_csvs/ \
  --output-dir path/to/position_filtered_csvs/ \
  --method x \
  --threshold 15
```

### 4. Interpolation
Interpolate missing coordinate values (NaNs) up to a maximum gap size using various spline or linear methods.

**Single-File Mode**
```bash
python refineDLC/interpolate.py \
  --input path/to/position_filtered.csv \
  --output path/to/interpolated_data.csv \
  --method cubic \
  --max_gap 5
```

**Batch-Directory Mode**
```bash
python refineDLC/interpolate.py \
  --input-dir path/to/position_filtered_csvs/ \
  --output-dir path/to/interpolated_csvs/ \
  --method cubic \
  --max_gap 5
```

## Example Workflow
Combine all steps in sequence:
```bash
python refineDLC/clean_coordinates.py --input raw.csv --output cleaned.csv --exclude "part1,part2"
python refineDLC/likelihood_filter.py --input cleaned.csv --output likelihood.csv --threshold 0.6
python refineDLC/position_filter.py --input-dir ./likelihood/ --output-dir ./position/ --method euclidean --threshold 30
python refineDLC/interpolate.py --input-dir ./position/ --output-dir ./interpolated/ --method cubic --max_gap 5
```

## Preprint
A preprint describing this pipeline is available on bioRxiv:

Weronika Klecel, Hadley Rahael, Samantha A. Brooks (2025). *refineDLC: an advanced post-processing pipeline for DeepLabCut outputs*. bioRxiv. https://doi.org/10.1101/2025.04.09.648046

## Repository Structure
```
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

—
*RefineDLC provides a standardized, automated post-processing workflow for DeepLabCut outputs, enhancing reproducibility and efficiency in kinematic analyses.*
