"""Aggregate input counts without retaining typed keys or key sequences."""

from collections import deque


# This is the same set of distinct virtual keys used by the working overlay.
# In particular, generic Shift/Ctrl/Alt are omitted because their left/right
# variants are polled separately. Mouse buttons are deliberately separate.
KEYBOARD_VKS = tuple(sorted({
    0x08, 0x09, 0x0D, 0x13, 0x14, 0x1B, 0x20,
    *range(0x21, 0x29), 0x2C, 0x2D, 0x2E,
    *range(0x30, 0x3A), *range(0x41, 0x5B),
    0x5B, 0x5C, 0x5D,
    *range(0x60, 0x6A), 0x6A, 0x6B, 0x6D, 0x6E, 0x6F,
    *range(0x70, 0x7C), 0x90, 0x91,
    *range(0xA0, 0xA6), *range(0xBA, 0xC1),
    *range(0xDB, 0xDF),
}))

MOUSE_BUTTON_VKS = (0x01, 0x02, 0x04, 0x05, 0x06)  # L/R/M/X1/X2


class InputCounter:
    """Count new down-edges; KPS uses only keyboard edges in the last second."""

    def __init__(self, total=0):
        self.total = max(0, int(total))
        self._previous_keys = set()
        self._previous_mouse = set()
        self._recent_keys = deque()

    def sample(self, keys, mouse_buttons, now):
        keys = set(keys)
        mouse_buttons = set(mouse_buttons)
        key_hits = len(keys - self._previous_keys)
        mouse_hits = len(mouse_buttons - self._previous_mouse)
        self._previous_keys = keys
        self._previous_mouse = mouse_buttons
        self.total += key_hits + mouse_hits
        self._recent_keys.extend([now] * key_hits)
        cutoff = now - 1.0
        while self._recent_keys and self._recent_keys[0] <= cutoff:
            self._recent_keys.popleft()
        return key_hits + mouse_hits

    @property
    def kps(self):
        return len(self._recent_keys)
