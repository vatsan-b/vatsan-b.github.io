#!/usr/bin/env python3
"""Contract for the About-page research focus cards."""

from pathlib import Path
import unittest


SOURCE = Path(__file__).resolve().parent.parent / "about.qmd"


class FocusCardTests(unittest.TestCase):
    def test_cards_are_non_routing_disclosure_controls_with_project_overviews(self):
        source = SOURCE.read_text(encoding="utf-8")

        self.assertNotIn('href="research.qmd#', source)
        self.assertEqual(source.count('class="focus-card"'), 4)
        self.assertIn('<button class="focus-card" type="button"', source)
        for description in (
            "torsion-resistant structures",
            "flexible tactile sensing",
            "sensorized grippers",
            "contact-sensitive manipulation",
        ):
            self.assertIn(description, source)

    def test_cards_reveal_on_hover_focus_and_touch_with_escape_close(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('.focus-card:hover', source)
        self.assertIn('.focus-card:focus-visible', source)
        self.assertIn('.focus-card.is-expanded', source)
        self.assertIn('event.key === "Escape"', source)


if __name__ == "__main__":
    unittest.main()
