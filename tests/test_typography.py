#!/usr/bin/env python3
"""Typography contract for the site-wide main body font."""

from pathlib import Path
import unittest


STYLES = Path(__file__).resolve().parent.parent / "styles.css"


class TypographyTests(unittest.TestCase):
    def test_body_uses_the_configured_adobe_source_serif_web_font(self):
        styles = STYLES.read_text(encoding="utf-8")
        self.assertIn('@import url("https://use.typekit.net/btj4xog.css")', styles)
        self.assertIn('--main-font:     "source-serif-4", Georgia, serif;', styles)


if __name__ == "__main__":
    unittest.main()
