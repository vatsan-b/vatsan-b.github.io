#!/usr/bin/env python3
"""Contract tests for the source and rendered galleries on ``for-fun``.

These tests deliberately check public markup and dependency contracts rather than
the precise names of implementation functions.  Run with:

    python3 -m unittest tests.test_for_fun_gallery_contract -v
"""

from html.parser import HTMLParser
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit


REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_PATH = REPO_ROOT / "for-fun.qmd"
RENDERED_PATH = REPO_ROOT / "docs" / "for-fun.html"
IMPLEMENTATION_PATH = REPO_ROOT / "assets" / "gallery" / "gallery.js"


class _DocumentParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag.lower(), dict(attrs)))


def _classes(attrs):
    return set((attrs.get("class") or "").split())


def _is_gallery_root(attrs):
    classes = _classes(attrs)
    return (
        "data-gallery" in attrs
        or "data-pswp-gallery" in attrs
        or "pswp-gallery" in classes
        or "fj-gallery" in classes
    ) and not ({"gallery-item", "fj-gallery-item"} & classes)


class ForFunSourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE_PATH.read_text(encoding="utf-8")
        cls.lower_source = cls.source.lower()

    def test_source_has_no_lightgallery_or_license_key(self):
        self.assertNotIn("lightgallery", self.lower_source)
        self.assertNotRegex(self.lower_source, r"license\s*key")

    def test_gallery_dependencies_are_self_hosted_photoswipe_and_fjgallery(self):
        self.assertIn("photoswipe", self.lower_source)
        self.assertRegex(self.lower_source, r"fjgallery|flickr-justified-gallery")
        self.assertNotRegex(self.lower_source, r"(?:cdn\.jsdelivr\.net|cdnjs\.cloudflare\.com)")

        dependency_tags = re.findall(
            r"<(?:script|link)\b[^>]*(?:photoswipe|fjgallery|flickr-justified-gallery)[^>]*>",
            self.source,
            flags=re.IGNORECASE,
        )
        self.assertGreaterEqual(len(dependency_tags), 4, "expected local CSS and JS for both libraries")
        for tag in dependency_tags:
            match = re.search(r"(?:src|href)=[\"']([^\"']+)", tag, flags=re.IGNORECASE)
            self.assertIsNotNone(match, tag)
            self.assertFalse(urlsplit(match.group(1)).scheme, f"gallery dependency is not local: {tag}")


class RenderedGalleryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = RENDERED_PATH.read_text(encoding="utf-8")
        cls.lower_html = cls.html.lower()
        parser = _DocumentParser()
        parser.feed(cls.html)
        cls.elements = parser.elements
        cls.implementation = IMPLEMENTATION_PATH.read_text(encoding="utf-8")

    def test_rendered_page_has_exactly_two_gallery_roots(self):
        roots = [attrs for _, attrs in self.elements if _is_gallery_root(attrs)]
        self.assertEqual(len(roots), 2, "Flight Simulation and Photography need one root each")
        self.assertEqual(len({attrs.get("id") for attrs in roots}), 2, "gallery roots need distinct IDs")

    def test_shared_implementation_creates_lazy_responsive_previews(self):
        # This site creates the gallery DOM from its generated manifest at
        # runtime, so the public contract belongs to the shared implementation,
        # not static HTML that Quarto cannot see.
        self.assertIn('loading="lazy"', self.implementation)
        self.assertIn('srcset="', self.implementation)
        self.assertIn('sizes="', self.implementation)
        self.assertIn("<picture>", self.implementation)
        self.assertIn("manifest.json", self.implementation)

    def test_photoswipe_markup_and_shared_configuration_are_present(self):
        self.assertIn("photoswipe", self.lower_html)
        self.assertRegex(self.implementation, r"data-pswp-(?:width|w)")
        self.assertRegex(self.implementation, r"data-pswp-(?:height|h)")
        self.assertRegex(self.implementation, r"PhotoSwipeLightbox\s*\(")
        self.assertEqual(
            len(re.findall(r"PhotoSwipeLightbox\s*\(", self.implementation)),
            1,
            "one shared PhotoSwipe setup should serve both gallery roots",
        )

    def test_rendered_gallery_dependencies_are_local_and_exist(self):
        gallery_refs = []
        for tag, attrs in self.elements:
            ref = attrs.get("src") if tag == "script" else attrs.get("href") if tag == "link" else None
            if ref and re.search(r"photoswipe|fjgallery|flickr-justified-gallery", ref, re.I):
                gallery_refs.append(ref)

        self.assertGreaterEqual(len(gallery_refs), 4, "expected local CSS and JS for both libraries")
        for ref in gallery_refs:
            parsed = urlsplit(ref)
            self.assertFalse(parsed.scheme or parsed.netloc, f"external gallery dependency: {ref}")
            local_path = (RENDERED_PATH.parent / unquote(parsed.path)).resolve()
            self.assertTrue(local_path.is_relative_to(REPO_ROOT.resolve()), f"dependency escapes repo: {ref}")
            self.assertTrue(local_path.is_file(), f"missing local dependency: {ref}")

    def test_no_obsolete_or_external_runtime_gallery_code(self):
        self.assertNotIn("lightgallery", self.lower_html)
        self.assertNotRegex(self.lower_html, r"license\s*key")
        for tag, attrs in self.elements:
            if tag != "script" or not attrs.get("src"):
                continue
            src = attrs["src"]
            if re.search(r"gallery|photoswipe|fjgallery", src, re.I):
                self.assertFalse(urlsplit(src).scheme, f"external runtime gallery script: {src}")


if __name__ == "__main__":
    unittest.main()
