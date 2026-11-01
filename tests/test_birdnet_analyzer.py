import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import birdnet_analyzer


class BirdNETAnalyzerAdapterTests(unittest.TestCase):
    def test_analyzer_csv_is_normalized(self):
        with tempfile.TemporaryDirectory() as temp:
            audio = Path(temp) / "sample.wav"
            audio.write_bytes(b"wav")
            csv_text = (
                "Start (s),End (s),Scientific name,Common name,Confidence,File\n"
                "0,3,Turdus migratorius,American Robin,0.91,sample.wav\n"
            )

            def fake_run(args, **kwargs):
                output_dir = Path(args[args.index("--output") + 1])
                (output_dir / "sample.BirdNET.results.csv").write_text(
                    csv_text, encoding="utf-8"
                )
                class Result:
                    returncode = 0
                    stdout = ""
                    stderr = ""
                return Result()

            with (
                patch.object(birdnet_analyzer, "BIRDNET_ENABLED", True),
                patch.object(birdnet_analyzer, "_analyzer_command", return_value="birdnet-analyze"),
                patch.object(birdnet_analyzer.subprocess, "run", side_effect=fake_run),
            ):
                results = birdnet_analyzer.analyze_audio(audio)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["label"], "American Robin")
        self.assertEqual(results[0]["scientific_name"], "Turdus migratorius")
        self.assertAlmostEqual(results[0]["confidence"], 0.91)
        self.assertEqual(results[0]["start_seconds"], 0.0)
        self.assertEqual(results[0]["end_seconds"], 3.0)


if __name__ == "__main__":
    unittest.main()
