# BongoCat Stats Overlay

A small **Windows-only** companion for [ayangweb/BongoCat](https://github.com/ayangweb/BongoCat). It adds a transparent, click-through `Keys` / `KPS` badge near the cat's lower-left corner without modifying BongoCat. This project is independent and is not affiliated with the upstream BongoCat project.

Version **0.1.0** has been tested with BongoCat v1.1.0 and Python 3.13 on Windows. Other BongoCat versions and Python versions have not yet been verified.

![BongoCat with the Keys and KPS badge](assets/demo.png)

## What it counts

- `Keys`: keyboard down-presses **plus** left/right/middle/X1/X2 mouse-button clicks, accumulated across restarts.
- `KPS`: keyboard down-presses during the latest rolling second. Mouse clicks do not change KPS.
- Holding a key or mouse button, including dragging, counts once until released and pressed again. Wheel scrolling is not counted.

The app checks Windows virtual-key states about every 25 ms. Extremely short presses or clicks can be missed. It counts input even while BongoCat is temporarily closed; the badge waits for the cat to return.

## Install and run

Install [ayangweb/BongoCat](https://github.com/ayangweb/BongoCat/releases) separately, then in PowerShell or Command Prompt inside this repository:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m bongocat_stats_overlay
```

After installation, `start.bat` starts the same app without a console. Use its `KPS` system-tray icon → **退出按键统计** to save and quit. Starting it twice will not start a second counter.

The program waits quietly if BongoCat is not yet running. If the cat closes and reopens, the badge is recreated and attached to its new window. It does not attach to the similarly named Steam BongoCat.

## Data and position

Runtime state is stored locally in `%LOCALAPPDATA%\BongoCatStatsOverlay\`:

- `stats.json` — the persistent aggregate total, saved about every five seconds and on normal exit.
- `config.json` — optional position offsets, created with defaults on first run.

`config.json` starts as:

```json
{
  "offset_x": 12,
  "offset_y": -62
}
```

The badge's top-left corner is positioned relative to BongoCat's bottom-left corner. Edit the two integer offsets and restart the overlay to move it. If `stats.json` is malformed, the original is preserved as `stats.corrupt-*.json` and a new total begins at zero; it is **not** silently overwritten. The file format is `{"total": 1234}`. An abrupt power loss may lose up to about five seconds of recent counts.

If migrating from the earlier `FullKeyboardBongoCat` prototype, quit that old stats helper first. Copy its current `keyboard_stats.json` total into the new `stats.json` before starting this program. Keep the old file as a backup and do not run both helpers at once.

## Privacy and limitations

The program reads global Windows virtual-key **states** to detect new presses. It briefly keeps the current/previous pressed-key sets in memory for edge detection, but writes only the aggregate `total` to disk. It does not save typed text, key sequences, window contents, or foreground app names, and its code makes no network requests. The BongoCat window is identified transiently by its title and executable name. Dependencies are downloaded during installation with `pip`, not by the running overlay.

The badge uses a cross-process Windows owned-window relationship to stay above BongoCat. Closing BongoCat destroys only that badge; the hidden controller keeps counting and recreates a new badge when the cat returns. This behavior is Windows-specific and should be retested after major BongoCat updates.

## Development and license

Run tests with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

MIT license. Some Win32 helpers are adapted from Bel1eve-qiu/desktop-pet under MIT; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). No BongoCat executable or model files are included; the screenshot only illustrates the separately installed app.
