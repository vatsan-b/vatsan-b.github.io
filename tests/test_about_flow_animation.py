#!/usr/bin/env python3
"""Regression contract for the Skills flow connector animation."""

from pathlib import Path
import re
import unittest


SOURCE = Path(__file__).resolve().parent.parent / "about.qmd"


class SkillsFlowAnimationTests(unittest.TestCase):
    def test_connectors_are_revealed_without_scroll_observer_gating(self):
        source = SOURCE.read_text(encoding="utf-8")
        # Connector visibility is essential information, not decoration: it
        # must not depend on scroll-restoration timing or observer delivery.
        self.assertNotIn("IntersectionObserver", source)
        self.assertRegex(
            source,
            re.compile(r"draw\(\);.*?requestAnimationFrame\(\(\)\s*=>\s*requestAnimationFrame\(play\)\)", re.DOTALL),
        )


if __name__ == "__main__":
    unittest.main()
