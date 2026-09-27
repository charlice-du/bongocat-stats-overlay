import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from bongocat_stats_overlay.config import OverlayConfig
from bongocat_stats_overlay.layout import BadgeMetrics, badge_metrics
from bongocat_stats_overlay.overlay import TkBadge


class LayoutTests(unittest.TestCase):
    def test_default_metrics_match_v01(self):
        self.assertEqual(badge_metrics(1.0),
                         BadgeMetrics(170, 50, 11, 14, 36, 10, 1))

    def test_badge_and_text_scale_together(self):
        self.assertEqual(badge_metrics(2.0),
                         BadgeMetrics(340, 100, 22, 28, 72, 20, 2))
        smaller = badge_metrics(0.75)
        self.assertEqual((smaller.width, smaller.height), (128, 38))
        self.assertEqual(smaller.font_size, 8)

    def test_tk_badge_uses_scaled_metrics_for_canvas_and_geometry(self):
        window = MagicMock()
        canvas = MagicMock()
        with (patch("bongocat_stats_overlay.overlay.tk.Toplevel",
                    return_value=window),
              patch("bongocat_stats_overlay.overlay.tk.Canvas",
                    return_value=canvas) as make_canvas,
              patch("bongocat_stats_overlay.overlay.hwnd_of", return_value=1),
              patch("bongocat_stats_overlay.overlay.attach_owner"),
              patch("bongocat_stats_overlay.overlay.set_click_through")):
            badge = TkBadge(object(), 2, OverlayConfig(scale=1.5))
            badge.place(SimpleNamespace(left=100, bottom=200))
            badge.draw(123, 4)

        self.assertEqual(make_canvas.call_args.kwargs["width"], 255)
        self.assertEqual(make_canvas.call_args.kwargs["height"], 75)
        window.geometry.assert_called_once_with("255x75+112+138")
        self.assertEqual(canvas.create_text.call_count, 2)
        self.assertEqual(canvas.create_text.call_args_list[0].kwargs["font"],
                         ("Segoe UI", 15, "bold"))
