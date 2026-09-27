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
                             {"offset_x": 12, "offset_y": -62, "scale": 1.0,
                              "count_mouse_clicks": True})

    def test_legacy_offset_file_keeps_default_scale_without_rewrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            original = '{"offset_x": -20, "offset_y": 40}'
            path.write_text(original, encoding="utf-8")
            self.assertEqual(load_config(path).config,
                             OverlayConfig(-20, 40, 1.0))
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_custom_scale(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text('{"offset_x": -20, "offset_y": 40, "scale": 1.5}',
                            encoding="utf-8")
            self.assertEqual(load_config(path).config,
                             OverlayConfig(-20, 40, 1.5))

    def test_mouse_counting_can_be_disabled(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(
                '{"offset_x": 12, "offset_y": -62, '
                '"count_mouse_clicks": false}', encoding="utf-8")
            self.assertEqual(load_config(path).config,
                             OverlayConfig(count_mouse_clicks=False))

    def test_bad_config_uses_defaults_without_destroying_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text('{"offset_x": true, "offset_y": -62}',
                            encoding="utf-8")
            result = load_config(path)
            self.assertEqual(result.config, OverlayConfig())
            self.assertIsNotNone(result.warning)
            self.assertIn("true", path.read_text(encoding="utf-8"))

    def test_invalid_scale_uses_defaults_without_destroying_file(self):
        for value in (True, "large", 0.5, 2.1, float("nan"), 10**1000):
            with self.subTest(scale=value), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "config.json"
                original = json.dumps({"offset_x": 12, "offset_y": -62,
                                       "scale": value})
                path.write_text(original, encoding="utf-8")
                result = load_config(path)
                self.assertEqual(result.config, OverlayConfig())
                self.assertIn("scale", result.warning)
                self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_invalid_mouse_flag_preserves_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            original = ('{"offset_x": 12, "offset_y": -62, '
                        '"count_mouse_clicks": 0}')
            path.write_text(original, encoding="utf-8")
            result = load_config(path)
            self.assertEqual(result.config, OverlayConfig())
            self.assertIn("count_mouse_clicks", result.warning)
            self.assertEqual(path.read_text(encoding="utf-8"), original)
