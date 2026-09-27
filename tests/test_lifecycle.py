from dataclasses import dataclass
import unittest

from bongocat_stats_overlay.lifecycle import BadgeLifecycle


@dataclass
class Target:
    hwnd: int
    visible: bool = True
    area: int = 100


class FakeBadge:
    def __init__(self, target):
        self.created_for = target.hwnd
        self.exists = True
        self.placements = []
        self.hidden = False
        self.drawn = []

    def alive(self):
        return self.exists

    def place(self, target):
        self.placements.append(target.hwnd)
        self.hidden = False

    def hide(self):
        self.hidden = True

    def draw(self, total, kps):
        self.drawn.append((total, kps))

    def close(self):
        self.exists = False


class LifecycleTests(unittest.TestCase):
    def test_absent_start_hidden_and_restart(self):
        created = []

        def factory(target):
            badge = FakeBadge(target)
            created.append(badge)
            return badge

        lifecycle = BadgeLifecycle(factory)
        lifecycle.update(None)
        self.assertEqual(created, [])
        lifecycle.update(Target(10))
        self.assertEqual(created[0].placements, [10])
        lifecycle.update(Target(10, visible=False))
        self.assertTrue(created[0].hidden)
        lifecycle.update(Target(10))
        self.assertEqual(len(created), 1)
        lifecycle.draw(17, 2)
        self.assertEqual(created[0].drawn, [(17, 2)])
        lifecycle.update(None)
        self.assertFalse(created[0].exists)
        lifecycle.update(Target(20))
        self.assertEqual(len(created), 2)
        self.assertEqual(lifecycle.owner_hwnd, 20)

    def test_external_owner_destruction_recreates_badge(self):
        created = []

        def factory(target):
            badge = FakeBadge(target)
            created.append(badge)
            return badge

        lifecycle = BadgeLifecycle(factory)
        lifecycle.update(Target(10))
        created[0].exists = False  # Windows destroyed the owned popup.
        lifecycle.update(Target(11))
        self.assertEqual(len(created), 2)
        self.assertEqual(created[1].placements, [11])

    def test_new_hwnd_replaces_old_badge(self):
        created = []

        def factory(target):
            badge = FakeBadge(target)
            created.append(badge)
            return badge

        lifecycle = BadgeLifecycle(factory)
        lifecycle.update(Target(1))
        lifecycle.update(Target(2))
        self.assertFalse(created[0].exists)
        self.assertEqual(created[1].created_for, 2)
