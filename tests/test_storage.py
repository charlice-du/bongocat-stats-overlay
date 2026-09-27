import json
from pathlib import Path
import tempfile
import unittest

from bongocat_stats_overlay.storage import (
    load_total, save_total, user_data_dir)


class StorageTests(unittest.TestCase):
    def test_location_uses_local_app_data(self):
        location = user_data_dir({"LOCALAPPDATA": r"C:\Test\Local"})
        self.assertEqual(location, Path(r"C:\Test\Local") / "BongoCatStatsOverlay")

    def test_missing_save_and_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data" / "stats.json"
            self.assertEqual(load_total(path).total, 0)
            save_total(1234, path)
            self.assertEqual(load_total(path).total, 1234)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")),
                             {"total": 1234})
            self.assertFalse(list(path.parent.glob("*.tmp")))

    def test_malformed_file_is_preserved_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stats.json"
            path.write_text("unfinished JSON", encoding="utf-8")
            result = load_total(path)
            self.assertEqual(result.total, 0)
            self.assertFalse(path.exists())
            self.assertTrue(result.corrupt_backup.exists())
            self.assertEqual(result.corrupt_backup.read_text(encoding="utf-8"),
                             "unfinished JSON")
            save_total(7, path)
            self.assertEqual(load_total(path).total, 7)
            self.assertTrue(result.corrupt_backup.exists())

    def test_invalid_total_is_quarantined(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stats.json"
            path.write_text('{"total": true}', encoding="utf-8")
            result = load_total(path)
            self.assertEqual(result.total, 0)
            self.assertIsNotNone(result.corrupt_backup)
