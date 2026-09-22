# Mobile and satellite radio communication systems

Python study simulations prepared around radio-communication topics. The runnable examples focus on mobile-network scenarios: base-station deactivation, cell-range expansion in a macro/micro network, and Massive MIMO MVDR beamforming. They are educational models, not network-planning or operational-control software.

## Included simulations

| Scenario | Script | Output |
| --- | --- | --- |
| Base-station deactivation | [Base_Station_Dealtivation.py](./Base%20Station%20Dealtivation/Base_Station_Dealtivation.py) | Compares traffic load, power use, and energy efficiency for one or two active stations. |
| Cell-range expansion | [Cell_Range_Extension.py](./Cell%20Range%20Extension/Cell_Range_Extension.py) | Calculates a macro/micro heterogeneous-network scenario and plots average throughput for selected CRE values. |
| Massive MIMO | [Massive_MIMO.py](./Massive%20MIMO/Massive_MIMO.py) | Interactively plots an MVDR beam pattern for a uniform linear array. |

## Quick start

Requirements: Python 3, NumPy, and Matplotlib.

~~~powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install numpy matplotlib
python ".\Base Station Dealtivation\Base_Station_Dealtivation.py"
~~~

Run either of the other two scripts from the repository root to reproduce its plot or interactive experiment. See [the scenario guide](docs/SCENARIOS.md) for the assumptions and inputs.

## Supported platform

The simulations are written in Python and can run wherever the listed dependencies are available. Matplotlib opens local charts, so a graphical Python environment is recommended.

## Scope and limitations

The values, formulas, and random seeds belong to compact coursework examples. They do not model all propagation effects, scheduling constraints, protocol behavior, or regulatory requirements. Validate and extend the model before using any result for an engineering decision.

## Documentation, license, and support

- [Scenario guide](docs/SCENARIOS.md)
- [Previous README archive](docs/archive/README-2026-09-16.md)
- [License](LICENSE.txt)
- Report a reproducible issue with the script name, Python version, and dependency versions.
