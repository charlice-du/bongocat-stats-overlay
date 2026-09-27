import unittest

from bongocat_stats_overlay.input_counter import (
    InputCounter, KEYBOARD_VKS, MOUSE_BUTTON_VKS)


class InputCounterTests(unittest.TestCase):
    def test_keyboard_mouse_and_rolling_kps(self):
        counter = InputCounter(100)
        self.assertEqual(counter.sample({0x41, 0x4A}, {0x01}, 10.0), 3)
        self.assertEqual((counter.total, counter.kps), (103, 2))
        self.assertEqual(counter.sample({0x41, 0x4A}, {0x01}, 10.1), 0)
        self.assertEqual(counter.sample({0x4A}, set(), 10.2), 0)
        self.assertEqual(counter.sample({0x41, 0x4A}, {0x01}, 10.3), 2)
        self.assertEqual((counter.total, counter.kps), (105, 3))
        self.assertEqual(counter.sample(set(), set(), 11.01), 0)
        self.assertEqual(counter.kps, 1)
        self.assertEqual(counter.sample(set(), set(), 11.31), 0)
        self.assertEqual(counter.kps, 0)

    def test_mouse_only_never_changes_kps(self):
        counter = InputCounter()
        self.assertEqual(counter.sample(set(), {0x02, 0x04, 0x05, 0x06}, 1), 4)
        self.assertEqual((counter.total, counter.kps), (4, 0))
        self.assertEqual(counter.sample(set(), {0x02, 0x04, 0x05, 0x06}, 2), 0)
        self.assertEqual(counter.sample(set(), set(), 3), 0)
        self.assertEqual(counter.sample(set(), {0x02}, 4), 1)

    def test_key_set_matches_legacy_without_duplicate_modifiers(self):
        self.assertEqual(len(KEYBOARD_VKS), 103)
        self.assertEqual(len(set(KEYBOARD_VKS)), len(KEYBOARD_VKS))
        self.assertFalse(set(KEYBOARD_VKS) & set(MOUSE_BUTTON_VKS))
        self.assertFalse({0x10, 0x11, 0x12} & set(KEYBOARD_VKS))
        self.assertTrue({0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5}
                        <= set(KEYBOARD_VKS))
