"""Manage the temporary owned badge separately from the long-lived app."""


class BadgeLifecycle:
    """Recreate a badge whenever BongoCat gets a new native window handle."""

    def __init__(self, badge_factory):
        self._badge_factory = badge_factory
        self.badge = None
        self.owner_hwnd = None

    def _discard(self):
        if self.badge is not None:
            self.badge.close()
        self.badge = None
        self.owner_hwnd = None

    def update(self, target):
        if self.badge is not None and not self.badge.alive():
            self._discard()

        if target is None:
            self._discard()
            return

        if self.badge is not None and self.owner_hwnd != target.hwnd:
            self._discard()

        if not target.visible or target.area <= 0:
            if self.badge is not None:
                self.badge.hide()
            return

        if self.badge is None:
            self.badge = self._badge_factory(target)
            self.owner_hwnd = target.hwnd
        self.badge.place(target)

    def draw(self, total, kps):
        if self.badge is not None and self.badge.alive():
            self.badge.draw(total, kps)

    def close(self):
        self._discard()
