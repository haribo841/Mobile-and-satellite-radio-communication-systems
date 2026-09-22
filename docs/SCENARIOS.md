# Scenario guide

## Base-station deactivation

[Base_Station_Dealtivation.py](../Base%20Station%20Dealtivation/Base_Station_Dealtivation.py) creates a repeatable three-user example by seeding Python's random generator. It compares:

- two active base stations; and
- one active station with the second station in sleep mode.

The script prints SNR values, requested rates, bandwidth occupancy, power, and a simple energy-efficiency ratio. It is a compact comparison model, not a radio-resource-management implementation.

## Cell-range expansion

[Cell_Range_Extension.py](../Cell%20Range%20Extension/Cell_Range_Extension.py) simulates a macro/micro topology with randomly distributed users and evaluates selected cell-range-expansion values. It uses NumPy for calculation and Matplotlib to draw a bar chart of average throughput.

The calculation uses free-space path loss and simplified bandwidth allocation. It should be treated as a learning visualization rather than a calibrated coverage prediction.

## Massive MIMO MVDR beamforming

[Massive_MIMO.py](../Massive%20MIMO/Massive_MIMO.py) calculates and plots an MVDR beam pattern for a uniform linear array. At launch it asks for the number of elements, element spacing, desired-signal direction, interfering directions, SNR, and INR. Press Enter at a prompt to keep the documented defaults.

## Reproducibility

Record the Python, NumPy, and Matplotlib versions when saving a result. The repository does not ship generated figures or a pinned dependency file, so charts should be recreated locally and labelled with the input assumptions.
