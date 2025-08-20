# refineDLC
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Overview

**refineDLC** is a modular, command-line toolkit for post‑processing DeepLabCut (DLC) coordinate outputs.
It comprises five standalone Python scripts—each supporting single-file and batch-directory modes:

- `clean_coordinates.py`
- `likelihood_filter.py`
- `position_filter.py`
- `interpolate.py`
- `plot_trajectories.py`

The toolkit standardizes cleaning, filtering, outlier removal, interpolation, and visualization of trajectories to improve reproducibility and interpretability of DLC-derived kinematic data.

**Key features**

- Single or batch processing for all steps
- Likelihood-based masking via global or **per‑bodypart** criteria (threshold or percentile)
- Positional outlier filtering via fixed thresholds or robust statistics
- Gap filling with linear or spline interpolation (bounded by user-defined maximum gap)
- Publication-ready trajectory and displacement plots
- Optional summary CSV for auditability (records applied cutoffs per file and bodypart)

---

## Installation

1. Ensure **Python 3.10+** is installed.
2. Create and activate a virtual environment (recommended).
3. Clone the repository.
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. (Optional) Install in editable mode:
   ```bash
   pip install -e .
   ```

---

## Requirements

- Python 3.10+
- pandas
- numpy
- scipy
- matplotlib

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

- `--input <FILE.csv>` : process a single CSV  
- `--input-dir <DIR>` : process all `*.csv` in the specified directory  

### Output Targets

- With `--input` → `--output <FILE.csv>`  
- With `--input-dir` → `--output-dir <DIR>`  

---

## Script Summaries

### 1. clean_coordinates.py

Pre-clean DLC outputs:

- Invert Y-values (optional, if image origin at top-left)
- Remove rows of all zeros
- Exclude specified landmarks

**Core options:**
- `--input/--input-dir`
- `--output/--output-dir`
- `--exclude "bp1,bp2,..."`

---

### 2. likelihood_filter.py

Mask coordinates based on DLC per-frame likelihoods. Supports multiple filtering strategies:

- **Global threshold**  
  `--threshold <VAL>` (0.0–1.0)  
  → All bodyparts with likelihood below `<VAL>` are masked.

- **Global percentile**  
  `--percentile <N>` (0–100)  
  → The lowest `N%` of likelihood values **per bodypart** are masked.

- **Per-bodypart thresholds (override global)**  
  `--threshold-per BODYPART=VAL` (repeatable)  
  → Apply a specific fixed threshold for selected bodyparts, e.g. `--threshold-per knee1=0.85`.

- **Per-bodypart percentiles (override global)**  
  `--percentile-per BODYPART=N` (repeatable)  
  → Apply a specific percentile-based cutoff for selected bodyparts, e.g. `--percentile-per withers=10`.

- **Summary reporting (optional)**  
  `--summary-csv <FILE>`  
  → Writes a wide-format CSV summarizing the *applied* criteria per bodypart and file.  
  • With `--percentile`/`--percentile-per`: records the **computed threshold value** (per bodypart).  
  • With `--threshold`/`--threshold-per`: records the **% frames removed** (per bodypart).

**Notes & precedence:**

- Per-bodypart flags override global settings.  
- If both a threshold and a percentile are provided for the **same** bodypart, the tool prefers the **threshold** and logs a warning.  
- This flexibility lets you enforce stricter filtering on sensitive landmarks (e.g., hooves, nostrils) while relaxing criteria on more stable ones (e.g., withers, midback).

**Core options:**
- `--input/--input-dir`
- `--output/--output-dir`
- `--threshold <0.0–1.0>` | `--percentile <0–100>`
- `--threshold-per BODYPART=VAL` (repeatable)
- `--percentile-per BODYPART=N` (repeatable)
- `--summary-csv <FILE>`

---

### 3. position_filter.py

Remove positional outliers using either fixed thresholds or robust statistics.

**Approaches:**
- Fixed displacement threshold: `--threshold <PX>`  
- Robust statistics: `--stat-method mad` or `--stat-method iqr`

**Core options:**
- `--input/--input-dir`
- `--output/--output-dir`
- `--method euclidean` (default)  
- `--threshold <PX>` (for fixed-threshold mode)  
- `--stat-method mad|iqr` (for robust mode)

---

### 4. interpolate.py

Fill NaN gaps up to `--max-gap` frames.

**Methods:**
- `--method linear`
- `--method cubic` (spline-based)

**Core options:**
- `--input/--input-dir`
- `--output/--output-dir`
- `--method linear|cubic`
- `--max-gap <INT>`

---

### 5. plot_trajectories.py

Generate displacement-over-time plots and/or 2D XY trajectory plots for specified bodyparts from DLC outputs with single-row headers (`<bodypart>_x`, `<bodypart>_y`, `<bodypart>_likelihood`).

**Core options:**
- `--input/--input-dir`
- `--bodyparts "bp1,bp2,..."`  
- `--output-dir <DIR>` (required)
- `--color <str>` (default: `"blue"`)
- `--plot-displacement`
- `--plot-trajectory`  
  *(if neither flag is provided, both are generated)*

---

## Examples

### Full pipeline on single files

```bash
python refineDLC/clean_coordinates.py --input raw.csv --output cleaned.csv --exclude "nose,tail"
python refineDLC/likelihood_filter.py --input cleaned.csv --output lik.csv --threshold 0.6 --summary-csv lik_summary.csv
python refineDLC/position_filter.py --input lik.csv --output pos.csv --method euclidean --threshold 30
python refineDLC/interpolate.py --input pos.csv --output interp.csv --method cubic --max-gap 5
```

### Batch pipeline

```bash
python refineDLC/clean_coordinates.py --input-dir raw_csvs/ --output-dir cleaned_csvs/ --exclude "elbow,knee"
python refineDLC/likelihood_filter.py --input-dir cleaned_csvs/ --output-dir lik_csvs/ --threshold 0.6 --summary-csv lik_summary.csv
python refineDLC/position_filter.py --input-dir lik_csvs/ --output-dir pos_csvs/ --method euclidean --stat-method mad
python refineDLC/interpolate.py --input-dir pos_csvs/ --output-dir interp_csvs/ --method linear --max-gap 3
```

### Percentile-based filtering

```bash
python refineDLC/likelihood_filter.py --input cleaned.csv --output filtered.csv --percentile 10 --summary-csv lik_summary.csv
```

### Per-bodypart thresholds

```bash
python refineDLC/likelihood_filter.py --input cleaned.csv --output filtered.csv   --threshold-per knee1=0.85 --threshold-per nostril=0.60 --summary-csv lik_summary.csv
```

### Per-bodypart percentiles (with global default)

```bash
python refineDLC/likelihood_filter.py --input-dir cleaned_csvs/ --output-dir filtered_csvs   --percentile 5 --percentile-per withers=10 --percentile-per poll=2 --summary-csv lik_summary.csv
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
bioRxiv. https://doi.org/10.1101/2025.04.09.648046

---

## Data Availability

The datasets used for validation of the presented software are available on Zenodo: https://doi.org/10.5281/zenodo.15186150

---


