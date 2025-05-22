# refineDLC

## Overview

**refineDLC** is a modular, command-line based toolkit for post-processing DeepLabCut coordinate outputs. It comprises four standalone Python scripts: `clean_coordinates.py`, `likelihood_filter.py`, `position_filter.py`, and `interpolate.py`—each supporting single-file and batch-directory modes. This pipeline enhances reproducibility by standardizing cleaning, filtering, outlier removal, and interpolation.

## Installation

1. Ensure **Python 3.10+** is installed.
2. Create and activate a virtual environment (highly recommended):

   ```bash
   python3 -m venv refineDLC
   source refineDLC/bin/activate   # Mac/Linux
   refineDLC\\Scripts\\activate  # Windows
   ```
   
3. **Clone the repository** into your activated environment:
   
   ```bash
   git clone https://github.com/wer-kle/refineDLC.git
   cd refineDLC
   ```
   
4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
5. (Optional) Install in editable mode:

   ```bash
   pip install -e .
   ```

## Requirements

* Python 3.10 or higher
* pandas
* numpy
* scipy
* matplotlib

## Repository Structure

```
refineDLC/
├── README.md
├── setup.py
├── requirements.txt
├── LICENSE
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

## Usage

All scripts are invocable via:

```bash
python -m refineDLC.<script_name> [OPTIONS]
```

or directly:

```bash
python refineDLC/<script_name>.py [OPTIONS]
```

### Input Modes (mutually exclusive)

* `--input <FILE.csv>`

  * Process a single CSV.
* `--input-dir <DIR>`

  * Process all `*.csv` in the specified directory.

### Output Targets

* With `--input`, specify:

  * `--output <FILE.csv>`
* With `--input-dir`, specify:

  * `--output-dir <DIR>`

### Script Summaries

#### 1. clean\_coordinates.py

Invert Y-values, remove rows of all zeros, and exclude specified landmarks.

**Options**

* `--input/--input-dir`
* `--output/--output-dir`
* `--exclude "part1,part2,..."`

#### 2. likelihood\_filter.py

Mask coordinates where likelihood < threshold.

**Options**

* `--input/--input-dir`
* `--output/--output-dir`
* `--threshold <float>` (default: 0.7)

#### 3. position\_filter.py

Remove positional outliers by fixed threshold or robust statistics.

**Options**

* `--input/--input-dir`
* `--output/--output-dir`
* `--method <euclidean|x|y>`
* Mutually exclusive:

  * `--threshold <float>` (fixed)
  * `--stat-method <mad|iqr>`
* Additional (robust):

  * `--mad-threshold <float>` (default: 3.5)
  * `--iqr-multiplier <float>` (default: 1.5)

#### 4. interpolate.py

Interpolate NaN gaps up to `max_gap` frames using linear or spline.

**Options**

* `--input/--input-dir`
* `--output/--output-dir`
* `--method <linear|cubic|spline>`
* `--max-gap <int>`

## Examples

1. **Full pipeline on single files**

```bash
python refineDLC/clean_coordinates.py --input raw.csv --output cleaned.csv --exclude "nose,tail"
python refineDLC/likelihood_filter.py --input cleaned.csv --output lik.pdf --threshold 0.6
python refineDLC/position_filter.py --input lik.csv --output pos.csv --method euclidean --threshold 30
python refineDLC/interpolate.py --input pos.csv --output interp.csv --method cubic --max-gap 5
```

2. **Batch pipeline**

```bash
python refineDLC/clean_coordinates.py --input-dir raw_csvs/ --output-dir cleaned_csvs/ --exclude "elbow,knee"
python refineDLC/likelihood_filter.py --input-dir cleaned_csvs/ --output-dir lik_csvs/ --threshold 0.6
python refineDLC/position_filter.py --input-dir lik_csvs/ --output-dir pos_csvs/ --method euclidean --stat-method mad
python refineDLC/interpolate.py --input-dir pos_csvs/ --output-dir interp_csvs/ --method linear --max-gap 3
```

## Citation

Weronika Klecel, Hadley Rahael, Samantha A. Brooks (2025). *refineDLC: an advanced post-processing pipeline for DeepLabCut outputs*. bioRxiv. [https://doi.org/10.1101/2025.04.09.648046](https://doi.org/10.1101/2025.04.09.648046)

---
