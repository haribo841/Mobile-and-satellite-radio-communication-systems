"""Regression checks for the documented, headless example capture."""

from pathlib import Path
import tempfile
import unittest

from render_examples import render_examples


class ExampleCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="radio-examples-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.output = Path(cls.temporary.name)
        cls.report = render_examples(cls.output)

    def test_expected_artifacts(self):
        for name in ("cell-range-expansion.png", "mvdr-defaults.png"):
            with self.subTest(name=name):
                data = (self.output / "images" / name).read_bytes()
                self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                self.assertGreater(len(data), 10000)
        self.assertTrue((self.output / "examples" / "results.json").is_file())

    def test_cre_result_shape(self):
        result = self.report["cell_range_expansion"]
        self.assertEqual(result["cre_db"], [0, 3, 6, 12])
        self.assertEqual(result["users"], 20)
        self.assertEqual(len(result["average_rate_mbps"]), 4)
        self.assertTrue(all(rate > 0 for rate in result["average_rate_mbps"]))

    def test_default_mvdr_and_station_output(self):
        result = self.report["mvdr"]
        self.assertEqual(result["elements"], 8)
        self.assertEqual(result["spacing_wavelengths"], 0.5)
        self.assertEqual(result["interferer_angles_degrees"], [-30.0, -15.0, 15.0, 30.0])
        self.assertEqual(result["angular_samples"], 361)
        self.assertAlmostEqual(result["normalized_peak_db"], 0.0)
        output = (self.output / "examples" / "base-station-output.txt").read_text(encoding="utf-8")
        self.assertIn("SNR1 [dB]:", output)
        self.assertIn("Scenariusz (a)", output)
        self.assertIn("Scenariusz (b)", output)


if __name__ == "__main__":
    unittest.main()
