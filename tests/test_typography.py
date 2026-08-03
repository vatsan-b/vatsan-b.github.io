#!/usr/bin/env python3
"""Typography contract for the site-wide main body font."""

from pathlib import Path
import unittest


STYLES = Path(__file__).resolve().parent.parent / "styles.css"


class TypographyTests(unittest.TestCase):
    def test_body_uses_the_central_main_font_variable(self):
        styles = STYLES.read_text(encoding="utf-8")
        self.assertIn("--main-font:", styles)
        self.assertIn("font-family: var(--main-font) !important;", styles)

    def test_navbar_uses_source_sans_as_a_legible_serif_contrast(self):
        styles = STYLES.read_text(encoding="utf-8")
        self.assertIn("family=Source+Sans+3", styles)
        self.assertIn('--font-nav:      "Source Sans 3", sans-serif;', styles)
        self.assertIn("font-family: var(--font-nav);", styles)


if __name__ == "__main__":
    unittest.main()
