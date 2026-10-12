
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database
import main
from process_audio import process_audio


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        root = Path(self.temp.name)

        data_patch = patch.object(database, "DATA_DIR", root / "data")
        db_patch = patch.object(
            database, "DATABASE_PATH", root / "data" / "test.db"
        )

        data_patch.start()
        db_patch.start()
        self.addCleanup(data_patch.stop)
        self.addCleanup(db_patch.stop)

        database.initialize_database()

    def test_recording_and_detection_are_saved(self):
        recording_id = database.save_recording(
            "test.wav",
            {"duration_seconds": 30.0, "size_bytes": 120000},
            {
                "timestamp": "2026-10-12T12:00:00",
                "cpu_temperature_c": None,
                "audio_rms": 250.0,
                "audio_peak": 900,
                "sound_level": "quiet",
            },
        )

        database.save_detection(
            recording_id,
            {
                "model_name": "YAMNet",
                "category": "environmental",
                "label": "Bird",
                "confidence": 0.82,
                "start_seconds": 2.0,
                "end_seconds": 5.0,
            },
        )

        recordings = database.recent_recordings()
        detections = database.recent_detections()

        self.assertEqual(len(recordings), 1)
        self.assertEqual(recordings[0]["duration_seconds"], 30.0)
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0]["model_name"], "YAMNet")
        self.assertEqual(detections[0]["species"], "Bird")
        self.assertAlmostEqual(detections[0]["confidence"], 0.82)


class PipelineTests(unittest.TestCase):
    def test_missing_audio_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            missing = Path(temp) / "missing.wav"

            with self.assertRaisesRegex(
                RuntimeError, "missing or too small"
            ):
                process_audio(missing)

    def test_birdnet_runs_even_if_yamnet_fails(self):
        audio_path = Path("fake-recording.wav")

        bird_detection = {
            "model_name": "BirdNET",
            "category": "bird",
            "label": "Robin",
            "confidence": 0.91,
            "start_seconds": 1.0,
            "end_seconds": 3.0,
        }

        with (
            patch.object(main, "record_audio", return_value=audio_path),
            patch.object(
                main,
                "process_audio",
                return_value={
                    "duration_seconds": 30.0,
                    "size_bytes": 120000,
                },
            ),
            patch.object(
                main,
                "read_environment",
                return_value={
                    "cpu_temperature_c": None,
                    "audio_rms": 200.0,
                    "audio_peak": 500,
                    "sound_level": "quiet",
                },
            ),
            patch.object(main, "save_recording", return_value=42),
            patch.object(main, "save_detection") as save_detection,
            patch.object(
                main,
                "analyze_environmental_sounds",
                side_effect=RuntimeError("simulated YAMNet failure"),
            ),
            patch.object(
                main, "analyze_birds", return_value=[bird_detection]
            ),
        ):
            returned_path, detections = main.run_once()

        self.assertEqual(returned_path, audio_path)
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0]["label"], "Robin")
        save_detection.assert_called_once_with(42, bird_detection)


if __name__ == "__main__":
    unittest.main(verbosity=2)
