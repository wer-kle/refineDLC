#!/usr/bin/env python3
"""
Trajectory plotting utilities for DeepLabCut single-row-header CSVs.

This CLI reads DeepLabCut CSV files with columns named:
  <bodypart>_x, <bodypart>_y, <bodypart>_likelihood
and produces:
  - Displacement-over-time plots (pixels per frame)
  - 2D XY trajectory plots (pixel coordinates)
for one or more bodyparts.

If neither --plot-displacement nor --plot-trajectory is provided, both are produced.
"""
import argparse
import os
from typing import List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ---- Plot styling constants ----
LABEL_FONTSIZE = 14
TICK_FONTSIZE = 12
TITLE_FONTSIZE = 16
LINEWIDTH = 2.0


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate displacement-over-time and/or 2D XY trajectory plots for specified bodyparts "
            "from DeepLabCut single-row-header CSV files."
        )
    )
    group_input = parser.add_mutually_exclusive_group(required=True)
    group_input.add_argument("--input", help="Path to a single DLC CSV file.")
    group_input.add_argument("--input-dir", help="Path to a directory containing DLC CSV files.")
    parser.add_argument(
        "--bodyparts",
        required=True,
        help="Comma-separated bodypart names exactly as they appear before the '_x'/'_y' suffixes.",
    )
    parser.add_argument("--color", default="blue", help="Matplotlib color name or hex code for lines.")
    parser.add_argument("--plot-displacement", action="store_true", help="Generate only displacement plots.")
    parser.add_argument("--plot-trajectory", action="store_true", help="Generate only 2D XY trajectory plots.")
    parser.add_argument("--output-dir", required=True, help="Directory where plots will be saved (created if missing)." )
    return parser.parse_args()


def load_dlc_data(csv_path: str) -> pd.DataFrame:
    """Load a DLC CSV with a single-row header. Expect <bodypart>_x, <bodypart>_y, <bodypart>_likelihood."""
    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError(f"CSV has no rows: {csv_path}")
    return df


def compute_displacement(df: pd.DataFrame, bodypart: str) -> np.ndarray:
    """Compute Euclidean displacement between consecutive frames for a given bodypart."""
    x_col = f"{bodypart}_x"
    y_col = f"{bodypart}_y"
    if x_col not in df.columns or y_col not in df.columns:
        raise KeyError(f"Missing required columns for bodypart '{bodypart}': '{x_col}', '{y_col}'")
    x = df[x_col].to_numpy(dtype=float)
    y = df[y_col].to_numpy(dtype=float)
    dx = np.diff(x)
    dy = np.diff(y)
    return np.sqrt(dx * dx + dy * dy)


def plot_displacement(displacement: np.ndarray, bodypart: str, color: str, out_path: str) -> None:
    plt.figure()
    plt.plot(np.arange(1, len(displacement) + 1), displacement, linewidth=LINEWIDTH, label=bodypart, color=color)
    plt.xlabel("Frame", fontsize=LABEL_FONTSIZE)
    plt.ylabel("Displacement (pixels/frame)", fontsize=LABEL_FONTSIZE)
    plt.title(f"Displacement over time — {bodypart}", fontsize=TITLE_FONTSIZE)
    plt.xticks(fontsize=TICK_FONTSIZE)
    plt.yticks(fontsize=TICK_FONTSIZE)
    plt.legend(fontsize=TICK_FONTSIZE)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def plot_xy_trajectory(df: pd.DataFrame, bodypart: str, color: str, out_path: str) -> None:
    x_col = f"{bodypart}_x"
    y_col = f"{bodypart}_y"
    x = df[x_col].to_numpy(dtype=float)
    y = df[y_col].to_numpy(dtype=float)
    plt.figure()
    plt.plot(x, y, linewidth=LINEWIDTH, label=bodypart, color=color)
    plt.scatter([x[0]], [y[0]], s=30, label="start")
    plt.scatter([x[-1]], [y[-1]], s=30, label="end")
    plt.xlabel("X (pixels)", fontsize=LABEL_FONTSIZE)
    plt.ylabel("Y (pixels)", fontsize=LABEL_FONTSIZE)
    plt.title(f"XY trajectory — {bodypart}", fontsize=TITLE_FONTSIZE)
    plt.xticks(fontsize=TICK_FONTSIZE)
    plt.yticks(fontsize=TICK_FONTSIZE)
    plt.legend(fontsize=TICK_FONTSIZE)
    plt.axis("equal")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def process_file(csv_path: str, bodyparts: List[str], color: str, make_disp: bool, make_traj: bool, output_dir: str) -> None:
    df = load_dlc_data(csv_path)
    base = os.path.splitext(os.path.basename(csv_path))[0]
    for bp in bodyparts:
        bp_safe = bp.replace(" ", "_")
        if make_disp:
            try:
                disp = compute_displacement(df, bp)
            except KeyError as e:
                print(f"[{base}] Skipping displacement for '{bp}': {e}")
            else:
                out = os.path.join(output_dir, f"{base}_{bp_safe}_displacement.png")
                plot_displacement(disp, bp, color, out)
                print(f"Saved: {out}")
        if make_traj:
            x_col, y_col = f"{bp}_x", f"{bp}_y"
            if x_col not in df.columns or y_col not in df.columns:
                print(f"[{base}] Skipping trajectory for '{bp}': missing '{x_col}'/'{y_col}'")
            else:
                out = os.path.join(output_dir, f"{base}_{bp_safe}_xy_trajectory.png")
                plot_xy_trajectory(df, bp, color, out)
                print(f"Saved: {out}")


def main() -> None:
    args = parse_arguments()
    os.makedirs(args.output_dir, exist_ok=True)
    make_disp = args.plot_displacement or not (args.plot_displacement or args.plot_trajectory)
    make_traj = args.plot_trajectory or not (args.plot_displacement or args.plot_trajectory)
    if args.input:
        csv_files = [args.input]
    else:
        csv_files = [
            os.path.join(args.input_dir, f) for f in os.listdir(args.input_dir) if f.lower().endswith(".csv")
        ]
        if not csv_files:
            print(f"No CSV files found in: {args.input_dir}")
            return
    bodyparts = [bp.strip() for bp in args.bodyparts.split(",") if bp.strip()]
    if not bodyparts:
        raise ValueError("No bodyparts provided after parsing --bodyparts.")
    for csv_path in csv_files:
        if not os.path.isfile(csv_path):
            print(f"Skipping non-file: {csv_path}")
            continue
        try:
            process_file(csv_path, bodyparts, args.color, make_disp, make_traj, args.output_dir)
        except Exception as e:
            print(f"Error processing '{csv_path}': {e}")


if __name__ == "__main__":
    main()
