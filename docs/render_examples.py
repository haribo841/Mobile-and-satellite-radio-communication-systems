"""Capture the existing coursework examples without opening chart windows."""

import argparse
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import platform
import runpy
from unittest.mock import patch

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def render_examples(output_root):
    repository = Path(__file__).resolve().parents[1]
    sources = {
        "base_station": repository / "Base Station Dealtivation" / "Base_Station_Dealtivation.py",
        "cell_range": repository / "Cell Range Extension" / "Cell_Range_Extension.py",
        "mvdr": repository / "Massive MIMO" / "Massive_MIMO.py",
    }
    source_hashes = {
        name: hashlib.sha256(path.read_bytes()).hexdigest()
        for name, path in sources.items()
    }
    image_directory = output_root / "images"
    result_directory = output_root / "examples"
    image_directory.mkdir(parents=True, exist_ok=True)
    result_directory.mkdir(parents=True, exist_ok=True)

    station_output = io.StringIO()
    with redirect_stdout(station_output):
        runpy.run_path(str(sources["base_station"]), run_name="__main__")
    (result_directory / "base-station-output.txt").write_text(
        station_output.getvalue(), encoding="utf-8"
    )

    with patch.object(plt, "show"):
        cell_range = runpy.run_path(str(sources["cell_range"]), run_name="__main__")
        rates = np.asarray(cell_range["avg_rates"], dtype=float)
        if rates.shape != (4,) or not np.isfinite(rates).all():
            raise ValueError("The CRE example did not produce four finite results.")
        plt.gcf().savefig(image_directory / "cell-range-expansion.png", dpi=180, bbox_inches="tight")
        plt.close("all")

        with patch("builtins.input", return_value=""):
            mvdr = runpy.run_path(str(sources["mvdr"]), run_name="__main__")
        figure = plt.gcf()
        beam_values = np.asarray(figure.axes[0].lines[0].get_ydata(), dtype=float)
        if beam_values.shape != (361,) or not np.isfinite(beam_values).all():
            raise ValueError("The MVDR example did not produce 361 finite samples.")
        if not np.isclose(beam_values.max(), 0.0):
            raise ValueError("The MVDR plot is not normalized to a 0 dB maximum.")
        figure.savefig(image_directory / "mvdr-defaults.png", dpi=180, bbox_inches="tight")
        plt.close("all")

    for name, path in sources.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != source_hashes[name]:
            raise ValueError(f"A simulation source changed during capture: {name}")

    report = {
        "purpose": "Reproduction of the existing coursework output, not physical-model validation.",
        "environment": {
            "platform": platform.system(),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "matplotlib": matplotlib.__version__,
            "backend": matplotlib.get_backend(),
        },
        "source_sha256": source_hashes,
        "cell_range_expansion": {
            "random_seed": 42,
            "users": cell_range["n_users"],
            "cre_db": cell_range["CRE_values"],
            "average_rate_mbps": (rates / 1e6).tolist(),
        },
        "mvdr": {
            "elements": mvdr["L_elements"],
            "spacing_wavelengths": mvdr["d_lambda_ratio"],
            "desired_angle_degrees": mvdr["soi_direction"],
            "interferer_angles_degrees": mvdr["snoi_list"],
            "snr_db": mvdr["snr_db_val"],
            "inr_db": mvdr["inr_db_val"],
            "angular_samples": int(beam_values.size),
            "normalized_peak_db": float(beam_values.max()),
        },
    }
    (result_directory / "results.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, default=Path(__file__).resolve().parent,
        help="Output root for images/ and examples/; defaults to docs/.",
    )
    arguments = parser.parse_args()
    print(json.dumps(render_examples(arguments.output_dir), indent=2, ensure_ascii=False))
