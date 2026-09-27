"""Numerical and interface regression checks for the Sonar cleanup."""

from contextlib import redirect_stdout
import io
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

from render_examples import np, plt


REPOSITORY = Path(__file__).resolve().parents[1]
BASE_STATION = REPOSITORY / "Base Station Dealtivation" / "Base_Station_Dealtivation.py"
CELL_RANGE = REPOSITORY / "Cell Range Extension" / "Cell_Range_Extension.py"
MIMO = REPOSITORY / "Massive MIMO" / "Massive_MIMO.py"


def load_simulation(path):
    with patch.object(plt, "show"):
        try:
            return runpy.run_path(str(path))
        finally:
            plt.close("all")


class BaseStationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.simulation = load_simulation(BASE_STATION)

    def test_bandwidth_formula(self):
        bandwidth = self.simulation["compute_bandwidth_for_rate"]
        self.assertAlmostEqual(bandwidth(4.0, 0.0), 4.0)
        self.assertEqual(bandwidth(0.0, 10.0), 0.0)
        self.assertLess(bandwidth(4.0, 10.0), bandwidth(4.0, 0.0))

    def test_two_stations_only_require_the_serving_snr(self):
        result = self.simulation["scenario_two_stations"]([0.0, 0.0], [1.0, 2.0])
        self.assertAlmostEqual(result["rho1"], 0.25)
        self.assertAlmostEqual(result["rho2"], 0.3)
        self.assertAlmostEqual(result["TotalPower"], 922.31)
        self.assertAlmostEqual(result["TotalRate"], 13.0)
        self.assertAlmostEqual(result["EE"], 13.0 / 922.31)

    def test_one_station_only_requires_the_serving_snr(self):
        result = self.simulation["scenario_one_station"]([0.0, 0.0], [1.0, 2.0])
        self.assertAlmostEqual(result["rho1"], 0.55)
        self.assertEqual(result["Power2"], 100.0)
        self.assertAlmostEqual(result["TotalPower"], 562.31)
        self.assertAlmostEqual(result["TotalRate"], 13.0)
        self.assertAlmostEqual(result["EE"], 13.0 / 562.31)

    def test_default_console_output_is_unchanged(self):
        output = io.StringIO()
        with redirect_stdout(output):
            self.simulation["main"]()
        expected = (REPOSITORY / "docs" / "examples" / "base-station-output.txt").read_text(encoding="utf-8")
        self.assertEqual(output.getvalue(), expected)


class CellRangeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.simulation = load_simulation(CELL_RANGE)

    def test_seeded_generator_does_not_use_global_random_functions(self):
        with patch.object(np.random, "seed", side_effect=AssertionError("Global seed changed")), \
                patch.object(np.random, "uniform", side_effect=AssertionError("Legacy generator used")):
            simulation = load_simulation(CELL_RANGE)
        self.assertIsInstance(simulation["rng"], np.random.Generator)
        np.testing.assert_allclose(
            simulation["user_pos"][:3],
            [773.9560485559633, 438.8784397520523, 858.5979199113824],
            rtol=1e-12,
        )
        self.assertTrue(np.all((simulation["user_pos"] >= 0) & (simulation["user_pos"] < 1000)))

    def test_seeded_sample_and_results_are_reproducible(self):
        repeated = load_simulation(CELL_RANGE)
        np.testing.assert_array_equal(repeated["user_pos"], self.simulation["user_pos"])
        np.testing.assert_allclose(repeated["avg_rates"], self.simulation["avg_rates"], rtol=1e-12)

    def test_bandwidth_allocation_handles_an_empty_cell(self):
        allocate = self.simulation["bandwidth_per_user"]
        self.assertEqual(allocate(2, 5), (100000.0, 625000.0))
        self.assertEqual(allocate(0, 5), (100000.0, 0))
        self.assertEqual(allocate(2, 0), (0, 625000.0))


class MvdrTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.simulation = load_simulation(MIMO)

    def capture_pattern(self, snr_db=10.0):
        with patch.object(plt, "show"):
            try:
                self.simulation["plot_mvdr_beampattern"](
                    8, 0.5, 0.0, [-30.0, -15.0, 15.0, 30.0], snr_db, 10.0
                )
                return np.array(plt.gca().lines[0].get_ydata(), copy=True)
            finally:
                plt.close("all")

    def test_broadside_steering_vector(self):
        vector = self.simulation["steering_vector"](0.0, 8, 0.5)
        np.testing.assert_array_equal(vector, np.ones((8, 1), dtype=complex))

    def test_default_beampattern_preserves_the_pre_cleanup_result(self):
        actual = self.capture_pattern()
        indices = np.arange(0, 361, 30)
        expected = [
            -120.0, -26.33695667874264, -18.578321601545156, -23.61694964549126,
            -100.60686162127217, -67.5925695374728, 0.0, -67.5925695374729,
            -100.60686162127203, -23.616949645491324, -18.578321601545177,
            -26.336956678742784, -120.0,
        ]
        self.assertEqual(actual.shape, (361,))
        np.testing.assert_allclose(actual[indices], expected, rtol=1e-10, atol=1e-8)

    def test_snr_remains_a_label_without_changing_the_weights(self):
        np.testing.assert_array_equal(self.capture_pattern(-5.0), self.capture_pattern(30.0))

    def test_regularization_retries_after_a_singular_matrix(self):
        invert = np.linalg.inv
        with patch.object(np.linalg, "inv", side_effect=[np.linalg.LinAlgError("singular"), invert(np.eye(8))]) as mocked_inverse:
            pattern = self.capture_pattern()
        self.assertEqual(mocked_inverse.call_count, 2)
        self.assertTrue(np.isfinite(pattern).all())
        self.assertAlmostEqual(float(pattern.max()), 0.0)

    def test_invalid_cli_input_uses_defaults(self):
        output = io.StringIO()
        with patch("builtins.input", return_value="invalid"), patch.object(plt, "show"), redirect_stdout(output):
            try:
                namespace = runpy.run_path(str(MIMO), run_name="__main__")
                self.assertEqual(namespace["L_elements"], 8)
                self.assertEqual(namespace["snoi_list"], [-30.0, -15.0, 15.0, 30.0])
                self.assertIn("Używam wartości domyślnych", output.getvalue())
            finally:
                plt.close("all")


if __name__ == "__main__":
    unittest.main()
