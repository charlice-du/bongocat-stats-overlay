from pathlib import Path
import unittest
from unittest.mock import patch

from bongocat_stats_overlay.overlay import StatsApp


class TrayPathTests(unittest.TestCase):
    def test_open_path_uses_windows_association(self):
        path = Path(r"C:\Test\config.json")
        with patch("bongocat_stats_overlay.overlay.os.startfile") as start:
            StatsApp._open_path(path, "Could not open config")
        start.assert_called_once_with(str(path))

    def test_open_path_reports_os_error(self):
        with (patch("bongocat_stats_overlay.overlay.os.startfile",
                    side_effect=OSError("access denied")),
              patch("bongocat_stats_overlay.overlay.messagebox.showerror")
              as show_error):
            StatsApp._open_path(Path(r"C:\Test\config.json"),
                                "Could not open config")
        show_error.assert_called_once_with("Could not open config",
                                           "access denied")
