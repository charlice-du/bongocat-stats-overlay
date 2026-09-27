import json
from pathlib import Path
import tempfile
import unittest

from bongocat_stats_overlay.config import OverlayConfig, load_config


class ConfigTests(unittest.TestCase):
    def test_default_file_created(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "app" / "config.json"
            result = load_config(path)
            self.assertEqual(result.config, OverlayConfig(12, -62))
            self.assertIsNone(result.warning)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")),
                             {"offset_x": 12, "offset_y": -62})

    def test_custom_offset(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text('{"offset_x": -20, "offset_y": 40}',
                            encoding="utf-8")
            self.assertEqual(load_config(path).config, OverlayConfig(-20, 40))

    def test_bad_config_uses_defaults_without_destroying_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text('{"offset_x": true, "offset_y": -62}',
                            encoding="utf-8")
            result = load_config(path)
            self.assertEqual(result.config, OverlayConfig())
            self.assertIsNotNone(result.warning)
            self.assertIn("true", path.read_text(encoding="utf-8"))
