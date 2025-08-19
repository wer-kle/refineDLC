

# refineDLC
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Overview

**refineDLC** is a modular, command-line based toolkit for post-processing DeepLabCut coordinate outputs.
It comprises five standalone Python scripts:
`clean_coordinates.py`, `likelihood_filter.py`, `position_filter.py`, `interpolate.py`, and `plot_trajectories.py`—each supporting single-file and batch-directory modes.
This pipeline enhances reproducibility by standardizing cleaning, filtering, outlier removal, interpolation, and visualization of trajectories.

---

## Installation

1. Ensure **Python 3.10+** is installed.
2. Create and activate a virtual environment (highly recommended).
3. Clone the repository.
4. Install dependencies with `pip install -r requirements.txt`.
5. (Optional) Install in editable mode: `pip install -e .`

---

## Requirements

* Python 3.10 or higher
* pandas
* numpy
* scipy
* matplotlib

---

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
│   ├── interpolate.py
│   └── plot_trajectories.py
└── tests/
    ├── test_clean_coordinates.py
    ├── test_likelihood_filter.py
    ├── test_position_filter.py
    ├── test_interpolate.py
    └── test_plot_trajectories.py
```

---

## Usage

All scripts can be invoked via:

```bash
python -m refineDLC.<script_name> [OPTIONS]
```

or directly:

```bash
python refineDLC/<script_name>.py [OPTIONS]
```

### Input Modes (mutually exclusive)

* `--input <FILE.csv>` : process a single CSV
* `--input-dir <DIR>` : process all `*.csv` in the specified directory

### Output Targets

* With `--input` → `--output <FILE.csv>`
* With `--input-dir` → `--output-dir <DIR>`

---

## Script Summaries

### 1. clean\_coordinates.py

Invert Y-values, remove rows of all zeros, and exclude specified landmarks.

### 2. likelihood\_filter.py

Mask coordinates based on likelihood (threshold or percentile).

### 3. position\_filter.py

Remove positional outliers (threshold or robust statistics).

### 4. interpolate.py

Interpolate NaN gaps up to `max_gap` frames using linear or spline.

### 5. plot\_trajectories.py

Generate **displacement-over-time** plots and/or **2D XY trajectory** plots for specified bodyparts from DeepLabCut outputs with single-row headers (`<bodypart>_x`, `<bodypart>_y`, `<bodypart>_likelihood`).

**Options:**

* `--input/--input-dir`
* `--bodyparts "bp1,bp2,..."`
* `--output-dir <DIR>` (required)
* `--color <str>` (default: `"blue"`)
* `--plot-displacement`
* `--plot-trajectory`
  *(if neither flag is provided, both are generated)*

---

## Examples

### Full pipeline on single files

```bash
python refineDLC/clean_coordinates.py --input raw.csv --output cleaned.csv --exclude "nose,tail"
python refineDLC/likelihood_filter.py --input cleaned.csv --output lik.csv --threshold 0.6
python refineDLC/position_filter.py --input lik.csv --output pos.csv --method euclidean --threshold 30
python refineDLC/interpolate.py --input pos.csv --output interp.csv --method cubic --max-gap 5
```

### Batch pipeline

```bash
python refineDLC/clean_coordinates.py --input-dir raw_csvs/ --output-dir cleaned_csvs/ --exclude "elbow,knee"
python refineDLC/likelihood_filter.py --input-dir cleaned_csvs/ --output-dir lik_csvs/ --threshold 0.6
python refineDLC/position_filter.py --input-dir lik_csvs/ --output-dir pos_csvs/ --method euclidean --stat-method mad
python refineDLC/interpolate.py --input-dir pos_csvs/ --output-dir interp_csvs/ --method linear --max-gap 3
```

### Percentile-based filtering

```bash
python refineDLC/likelihood_filter.py --input cleaned.csv --output filtered.csv --percentile 10
```

### Trajectory plotting

```bash
# Single file, both displacement and trajectory
python refineDLC/plot_trajectories.py --input interp.csv --bodyparts withers,stifle --output-dir plots/

# Batch mode, displacement only, custom color
python refineDLC/plot_trajectories.py --input-dir interp_csvs/ --bodyparts withers,stifle --plot-displacement --color magenta --output-dir plots/
```

---

## Citation

Weronika Klecel, Hadley Rahael, Samantha A. Brooks (2025).
*refineDLC: an advanced post-processing pipeline for DeepLabCut outputs*.
bioRxiv. [https://doi.org/10.1101/2025.04.09.648046](https://doi.org/10.1101/2025.04.09.648046)

---

## Data availability

The datasets used for validation of the presented software are available on [Zenodo](https://doi.org/10.5281/zenodo.15186150).

---

