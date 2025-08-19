import pandas as pd
import numpy as np
import subprocess
import sys
from pathlib import Path
import importlib.util

SCRIPT = str(Path(__file__).parent.parent / "scripts" / "plot_displacements.py")
DATA = Path(__file__).parent / "data" / "dlc_single_header_disp.csv"


def test_compute_and_cli_overlay(tmp_path):
    spec = importlib.util.spec_from_file_location("plot_displacements", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore

    df = pd.read_csv(DATA)
    disps = mod.compute_displacements(df, ["withers", "stifle"], min_likelihood=None)
    for k, v in disps.items():
        assert np.allclose(v, np.sqrt(2.0))

    outdir = tmp_path / "plots"
    cmd = [
        sys.executable, SCRIPT,
        "--input", str(DATA),
        "--bodyparts", "withers,stifle",
        "--output-dir", str(outdir),
    ]
    subprocess.check_call(cmd)
    files = list(outdir.glob("*overlay.png"))
    assert len(files) == 1


def test_cli_per_bodypart_and_ma(tmp_path):
    outdir = tmp_path / "plots2"
    cmd = [
        sys.executable, SCRIPT,
        "--input", str(DATA),
        "--bodyparts", "withers,stifle",
        "--per-bodypart",
        "--moving-average", "3",
        "--output-dir", str(outdir),
        "--cumulative",
    ]
    subprocess.check_call(cmd)
    files = list(outdir.glob("*.png"))
    assert len(files) == 2
