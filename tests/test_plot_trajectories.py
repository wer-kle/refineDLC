import os
import pandas as pd
import numpy as np
import subprocess
import sys
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "scripts" / "plot_trajectories.py")
DATA = Path(__file__).parent / "data" / "dlc_single_header.csv"


def test_compute_displacement_smoke():
    # quick API smoke test by importing the module and calling the function
    import importlib.util
    spec = importlib.util.spec_from_file_location("plot_trajectories", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore

    df = pd.read_csv(DATA)
    disp = mod.compute_displacement(df, "withers")
    assert isinstance(disp, np.ndarray)
    assert len(disp) == len(df) - 1
    # Known simple pattern: coordinates increase by 1 each frame -> displacement == sqrt(2)
    assert np.allclose(disp, np.sqrt(2.0))


def test_cli_generates_pngs(tmp_path):
    outdir = tmp_path / "plots"
    cmd = [
        sys.executable, SCRIPT,
        "--input", str(DATA),
        "--bodyparts", "withers,stifle",
        "--output-dir", str(outdir),
        "--plot-displacement"
    ]
    subprocess.check_call(cmd)

    # Two bodyparts -> two PNGs
    files = list(outdir.glob("*.png"))
    assert len(files) == 2
    names = {p.name for p in files}
    assert any("withers_displacement" in n for n in names)
    assert any("stifle_displacement" in n for n in names)
