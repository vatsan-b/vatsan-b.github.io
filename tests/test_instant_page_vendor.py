#!/usr/bin/env python3
"""Contract for the self-hosted Instant.page runtime."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent.parent
LOCAL_PATH = "assets/vendor/instant-page/5.2.0/instantpage.js"
PAGES = ("index.html", "about.html", "research.html", "publications.html", "mentoring.html", "for-fun.html")


class InstantPageVendorTests(unittest.TestCase):
    def test_instant_page_is_local_and_rendered_pages_do_not_use_the_cdn(self):
        source_config = (ROOT / "_quarto.yml").read_text(encoding="utf-8")
        self.assertIn(LOCAL_PATH, source_config)
        self.assertNotIn("https://instant.page/", source_config)

        vendor_script = ROOT / LOCAL_PATH
        self.assertTrue(vendor_script.is_file())
        self.assertIn("instant.page v5.2.0", vendor_script.read_text(encoding="utf-8"))
        self.assertTrue(vendor_script.with_name("LICENSE").is_file())

        for page in PAGES:
            rendered = (ROOT / "docs" / page).read_text(encoding="utf-8")
            self.assertIn(LOCAL_PATH, rendered, page)
            self.assertNotIn("https://instant.page/", rendered, page)


if __name__ == "__main__":
    unittest.main()
