#!/usr/bin/env python3
"""
Plot frame-to-frame displacement time series from DeepLabCut single-row-header CSVs.

Expected columns per bodypart: <bodypart>_x, <bodypart>_y, and optionally <bodypart>_likelihood.
The tool can overlay multiple bodyparts in a single figure or emit one figure per bodypart.
"""
import argparse
import os
from typing import List, Dict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

LABEL_FONTSIZE = 14
TICK_FONTSIZE = 12
TITLE_FONTSIZE = 16
LINEWIDTH = 2.0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Plot frame-to-frame displacement for specified bodyparts from DLC single-row CSVs."
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--input", help="Path to a single DLC CSV file.")
    g.add_argument("--input-dir", help="Path to a directory containing DLC CSV files.")
    p.add_argument("--bodyparts", required=True,
                   help="Comma-separated list of bodypart names (before '_x'/'_y').")
    p.add_argument("--output-dir", required=True, help="Directory to save PNG plots.")
    p.add_argument("--min-likelihood", type=float, default=None,
                   help="If provided, frames with likelihood < threshold for a bodypart are masked before differencing.")
    p.add_argument("--moving-average", type=int, default=0,
                   help="Optional moving-average window size (in frames) applied to displacement time series.")
    p.add_argument("--per-bodypart", action="store_true",
                   help="Emit one PNG per bodypart instead of an overlay figure.")
    p.add_argument("--cumulative", action="store_true",
                   help="Additionally plot cumulative displacement (integral) for each series.")
    p.add_argument("--color-cycle", default=None,
                   help="Optional comma-separated list of matplotlib colors to cycle for bodyparts (overlay mode)." )
    return p.parse_args()


def _series_displacement(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    dx = np.diff(x)
    dy = np.diff(y)
    return np.sqrt(dx * dx + dy * dy)


def _moving_average(a: np.ndarray, k: int) -> np.ndarray:
    if k <= 1:
        return a
    k = int(k)
    if k < 1 or k > len(a):
        return a
    cumsum = np.cumsum(np.insert(a, 0, 0.0))
    return (cumsum[k:] - cumsum[:-k]) / k


def compute_displacements(df: pd.DataFrame, bodyparts: List[str], min_likelihood: float | None) -> Dict[str, np.ndarray]:
    out: Dict[str, np.ndarray] = {}
    for bp in bodyparts:
        x_col, y_col, l_col = f"{bp}_x", f"{bp}_y", f"{bp}_likelihood"
        if x_col not in df.columns or y_col not in df.columns:
            raise KeyError(f"Missing columns for bodypart '{bp}': '{x_col}', '{y_col}'")
        x = df[x_col].to_numpy(dtype=float)
        y = df[y_col].to_numpy(dtype=float)
        if min_likelihood is not None and l_col in df.columns:
            l = df[l_col].to_numpy(dtype=float)
            low = l < float(min_likelihood)
            x = x.copy(); y = y.copy()
            x[low] = np.nan
            y[low] = np.nan
        disp = _series_displacement(x, y)
        out[bp] = disp
    return out


def plot_overlay(displacements: Dict[str, np.ndarray], base_name: str, out_dir: str,
                 moving_average: int = 0, cumulative: bool = False,
                 color_cycle: List[str] | None = None) -> str:
    plt.figure()
    colors = None
    if color_cycle:
        colors = [c.strip() for c in color_cycle if c.strip()]
    for i, (bp, disp) in enumerate(displacements.items()):
        series = disp
        if moving_average and moving_average > 1:
            series = _moving_average(series, moving_average)
        x = np.arange(1, len(series) + 1)
        kw = {}
        if colors:
            kw["color"] = colors[i % len(colors)]
        plt.plot(x, series, linewidth=LINEWIDTH, label=bp, **kw)
        if cumulative:
            cum = np.nancumsum(series)
            plt.plot(x, cum, linewidth=LINEWIDTH, linestyle=":", label=f"{bp} (cumulative)", **kw)
    plt.xlabel("Frame", fontsize=LABEL_FONTSIZE)
    plt.ylabel("Displacement (pixels/frame)", fontsize=LABEL_FONTSIZE)
    ttl_extra = []
    if moving_average and moving_average > 1:
        ttl_extra.append(f"MA={moving_average}")
    if cumulative:
        ttl_extra.append("cum")
    extra = (" [" + ", ".join(ttl_extra) + "]") if ttl_extra else ""
    plt.title(f"Displacement — overlay{extra}", fontsize=TITLE_FONTSIZE)
    plt.xticks(fontsize=TICK_FONTSIZE)
    plt.yticks(fontsize=TICK_FONTSIZE)
    plt.legend(fontsize=TICK_FONTSIZE)
    plt.tight_layout()
    out_path = os.path.join(out_dir, f"{base_name}_displacement_overlay.png")
    plt.savefig(out_path, dpi=200)
    plt.close()
    return out_path


def plot_per_bodypart(displacements: Dict[str, np.ndarray], base_name: str, out_dir: str,
                      moving_average: int = 0, cumulative: bool = False) -> list[str]:
    out_paths: list[str] = []
    for bp, disp in displacements.items():
        series = disp
        if moving_average and moving_average > 1:
            series = _moving_average(series, moving_average)
        x = np.arange(1, len(series) + 1)
        plt.figure()
        plt.plot(x, series, linewidth=LINEWIDTH, label=bp)
        if cumulative:
            cum = np.nancumsum(series)
            plt.plot(x, cum, linewidth=LINEWIDTH, linestyle=":", label=f"{bp} (cumulative)")
        plt.xlabel("Frame", fontsize=LABEL_FONTSIZE)
        plt.ylabel("Displacement (pixels/frame)", fontsize=LABEL_FONTSIZE)
        ttl_extra = []
        if moving_average and moving_average > 1:
            ttl_extra.append(f"MA={moving_average}")
        if cumulative:
            ttl_extra.append("cum")
        extra = (" [" + ", ".join(ttl_extra) + "]") if ttl_extra else ""
        plt.title(f"Displacement — {bp}{extra}", fontsize=TITLE_FONTSIZE)
        plt.xticks(fontsize=TICK_FONTSIZE)
        plt.yticks(fontsize=TICK_FONTSIZE)
        plt.legend(fontsize=TICK_FONTSIZE)
        plt.tight_layout()
        out_path = os.path.join(out_dir, f"{base_name}_{bp}_displacement.png")
        plt.savefig(out_path, dpi=200)
        plt.close()
        out_paths.append(out_path)
    return out_paths


def main() -> None:
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    bodyparts = [b.strip() for b in args.bodyparts.split(",") if b.strip()]
    if args.input:
        files = [args.input]
    else:
        files = [os.path.join(args.input_dir, f) for f in os.listdir(args.input_dir) if f.lower().endswith(".csv")]
        if not files:
            print(f"No CSV files found in: {args.input_dir}")
            return
    for csv_path in files:
        if not os.path.isfile(csv_path):
            print(f"Skipping non-file: {csv_path}")
            continue
        try:
            df = pd.read_csv(csv_path)
            displacements = compute_displacements(df, bodyparts, args.min_likelihood)
            base = os.path.splitext(os.path.basename(csv_path))[0]
            if args.per_bodypart:
                outs = plot_per_bodypart(displacements, base, args.output_dir,
                                         moving_average=args.moving_average, cumulative=args.cumulative)
                for p in outs:
                    print(f"Saved: {p}")
            else:
                colors = args.color_cycle.split(",") if args.color_cycle else None
                outp = plot_overlay(displacements, base, args.output_dir,
                                    moving_average=args.moving_average, cumulative=args.cumulative,
                                    color_cycle=colors)
                print(f"Saved: {outp}")
        except Exception as e:
            print(f"Error processing '{csv_path}': {e}")


if __name__ == "__main__":
    main()
