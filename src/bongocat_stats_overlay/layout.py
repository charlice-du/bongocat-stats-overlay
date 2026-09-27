"""Pure badge sizing math; Tk and Win32 code consume these metrics."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BadgeMetrics:
    width: int
    height: int
    label_x: int
    total_y: int
    kps_y: int
    font_size: int
    border_width: int


def badge_metrics(scale):
    """Scale all badge dimensions together, preserving v0.1 at scale 1."""
    pixel = lambda value: round(value * scale)
    return BadgeMetrics(
        width=pixel(170),
        height=pixel(50),
        label_x=pixel(11),
        total_y=pixel(14),
        kps_y=pixel(36),
        font_size=max(1, pixel(10)),
        border_width=max(1, pixel(1)),
    )
