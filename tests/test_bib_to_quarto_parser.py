#!/usr/bin/env python3
"""Tests for scripts/bib-to-quarto-parser.py.

Standard library only (unittest). Run with:
    python3 -m unittest discover -s tests -v

Covers:
  - visible-output preservation for the real, trusted publications.bib
  - escape_markdown neutralizing HTML/Quarto-markup injection in display fields
  - sanitize_url enforcing HTTPS-only, well-formed URLs and rejecting
    javascript:/data:/http:/malformed URLs
  - end-to-end hostile-fixture .bib entries being rejected by main()
"""

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "bib-to-quarto-parser.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("bib_to_quarto_parser", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


parser = _load_module()


class EscapeMarkdownTests(unittest.TestCase):
    def test_html_tags_are_neutralized(self):
        out = parser.escape_markdown("<script>alert(1)</script>")
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)
        self.assertIn("&lt;/script&gt;", out)

    def test_html_attribute_injection_neutralized(self):
        out = parser.escape_markdown('<img src=x onerror=alert(1)>')
        self.assertNotIn("<img", out)
        self.assertIn("&lt;img", out)
        self.assertIn("&gt;", out)

    def test_markdown_link_syntax_neutralized(self):
        out = parser.escape_markdown("[Click me](javascript:alert(1))")
        # brackets must be escaped so this can never parse as a markdown link
        self.assertNotIn("[Click me]", out)
        self.assertIn(r"\[Click me\]", out)

    def test_quarto_span_syntax_neutralized(self):
        out = parser.escape_markdown('[text]{.class onclick="alert(1)"}')
        self.assertIn(r"\[text\]", out)

    def test_emphasis_and_code_span_chars_escaped(self):
        out = parser.escape_markdown("*bold* _em_ `code`")
        self.assertEqual(out, r"\*bold\* \_em\_ \`code\`")

    def test_backslash_escaped_first_no_double_unescape(self):
        # a literal backslash in the source text must not combine with a
        # later-added escape backslash to produce an unescaped bracket
        out = parser.escape_markdown("\\[not a link\\]")
        # every bracket in the output must be immediately preceded by a
        # backslash (i.e. still escaped, never a bare markdown '[' or ']')
        i = 0
        while i < len(out):
            if out[i] in "[]":
                self.assertGreater(i, 0)
                self.assertEqual(out[i - 1], "\\")
            i += 1

    def test_plain_text_unaffected(self):
        out = parser.escape_markdown("Good, Ian and Balaji, Srivatsan")
        self.assertEqual(out, "Good, Ian and Balaji, Srivatsan")

    def test_ampersand_escaped(self):
        self.assertEqual(parser.escape_markdown("Smith & Sons"), "Smith &amp; Sons")


class SanitizeUrlTests(unittest.TestCase):
    def test_accepts_plain_https_url(self):
        url = "https://arxiv.org/abs/2501.09819"
        self.assertEqual(parser.sanitize_url(url, "url_arxiv", "t"), url)

    def test_accepts_https_url_with_path_query(self):
        url = "https://doi.org/10.1109/RoboSoft60065.2024.10521982"
        self.assertEqual(parser.sanitize_url(url, "url_ieee", "t"), url)

    def test_rejects_javascript_scheme(self):
        with self.assertRaises(ValueError):
            parser.sanitize_url("javascript:alert(1)", "url_pdf", "t")

    def test_rejects_javascript_scheme_case_variant(self):
        with self.assertRaises(ValueError):
            parser.sanitize_url("JaVaScRiPt:alert(1)", "url_pdf", "t")

    def test_rejects_data_scheme(self):
        with self.assertRaises(ValueError):
            parser.sanitize_url(
                "data:text/html,<script>alert(document.domain)</script>",
                "url_pdf",
                "t",
            )

    def test_rejects_plain_http(self):
        with self.assertRaises(ValueError):
            parser.sanitize_url("http://example.com/paper.pdf", "url_pdf", "t")

    def test_rejects_missing_scheme(self):
        with self.assertRaises(ValueError):
            parser.sanitize_url("evil.com/x", "url_pdf", "t")

    def test_rejects_ftp_scheme(self):
        with self.assertRaises(ValueError):
            parser.sanitize_url("ftp://example.com/x", "url_pdf", "t")

    def test_rejects_embedded_whitespace(self):
        with self.assertRaises(ValueError):
            parser.sanitize_url("https://example.com/ a", "url_pdf", "t")

    def test_rejects_leading_trailing_whitespace(self):
        with self.assertRaises(ValueError):
            parser.sanitize_url(" https://example.com/a", "url_pdf", "t")

    def test_rejects_control_characters(self):
        with self.assertRaises(ValueError):
            parser.sanitize_url("https://example.com/\x00x", "url_pdf", "t")

    def test_rejects_newline_injection(self):
        with self.assertRaises(ValueError):
            parser.sanitize_url("https://example.com/a\nEvil: header", "url_pdf", "t")

    def test_rejects_unbalanced_paren_link_breakout(self):
        # an unescaped ')' would prematurely close a markdown [label](url)
        with self.assertRaises(ValueError):
            parser.sanitize_url(
                "https://example.com/x)[click](https://evil.com",
                "url_pdf",
                "t",
            )

    def test_rejects_userinfo_host_confusion(self):
        with self.assertRaises(ValueError):
            parser.sanitize_url("https://trusted.com@evil.com/", "url_pdf", "t")

    def test_rejects_malformed_percent_encoding(self):
        with self.assertRaises(ValueError):
            parser.sanitize_url("https://example.com/%zz", "url_pdf", "t")

    def test_rejects_percent_encoded_control_char(self):
        with self.assertRaises(ValueError):
            parser.sanitize_url("https://example.com/%0d%0aEvil:%20x", "url_pdf", "t")

    def test_rejects_empty_url(self):
        with self.assertRaises(ValueError):
            parser.sanitize_url("", "url_pdf", "t")

    def test_rejects_bare_scheme_no_host(self):
        with self.assertRaises(ValueError):
            parser.sanitize_url("https://", "url_pdf", "t")


class RealBibRegressionTests(unittest.TestCase):
    """The hardened generator must not change output for the real, trusted
    publications.bib."""

    def test_generated_output_matches_committed_file(self):
        expected = (REPO_ROOT / "publications-parsed.qmd").read_text(encoding="utf-8")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            shutil.copy(REPO_ROOT / "publications.bib", tmp_path / "publications.bib")
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH)],
                cwd=tmp_path,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            actual = (tmp_path / "publications-parsed.qmd").read_text(encoding="utf-8")

        self.assertEqual(actual, expected)


class HostileFixtureEndToEndTests(unittest.TestCase):
    """Full pipeline (parse_bib -> render_entry / main) against hostile .bib
    fixtures: HTML injection in display fields, and javascript:/data: URLs."""

    def _run_generator(self, bib_text):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "publications.bib").write_text(bib_text, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH)],
                cwd=tmp_path,
                capture_output=True,
                text=True,
            )
            out_file = tmp_path / "publications-parsed.qmd"
            out_text = out_file.read_text(encoding="utf-8") if out_file.exists() else None
            return result.returncode, result.stdout, result.stderr, out_text

    def test_html_script_injection_in_title_is_neutralized(self):
        bib = """
@article{evil2024,
  title   = {Innocuous <script>alert(document.cookie)</script> Title},
  author  = {Evil, Doctor},
  journal = {Journal of Testing},
  year    = {2024}
}
"""
        code, out, err, text = self._run_generator(bib)
        self.assertEqual(code, 0, msg=err)
        self.assertIsNotNone(text)
        self.assertNotIn("<script>", text)
        self.assertIn("&lt;script&gt;", text)

    def test_html_img_onerror_injection_in_author_is_neutralized(self):
        bib = """
@article{evil2024b,
  title   = {A Normal Title},
  author  = {<img src=x onerror=alert(1)>, Evil},
  journal = {Journal of Testing},
  year    = {2024}
}
"""
        code, out, err, text = self._run_generator(bib)
        self.assertEqual(code, 0, msg=err)
        self.assertIsNotNone(text)
        self.assertNotIn("<img", text)

    def test_status_field_html_injection_is_neutralized(self):
        bib = """
@article{evil2024c,
  title  = {A Normal Title},
  author = {Normal, Author},
  year   = {2024},
  status = {<b onmouseover=alert(1)>Under Review</b>}
}
"""
        code, out, err, text = self._run_generator(bib)
        self.assertEqual(code, 0, msg=err)
        self.assertIsNotNone(text)
        self.assertNotIn("<b ", text)

    def test_javascript_url_is_rejected_and_build_fails(self):
        bib = """
@article{evil2024d,
  title   = {A Normal Title},
  author  = {Normal, Author},
  journal = {Journal of Testing},
  year    = {2024},
  url_pdf = {javascript:alert(document.domain)}
}
"""
        code, out, err, text = self._run_generator(bib)
        self.assertNotEqual(code, 0)
        self.assertIn("url_pdf", err)

    def test_data_url_is_rejected_and_build_fails(self):
        bib = """
@article{evil2024e,
  title    = {A Normal Title},
  author   = {Normal, Author},
  journal  = {Journal of Testing},
  year     = {2024},
  url_ieee = {data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==}
}
"""
        code, out, err, text = self._run_generator(bib)
        self.assertNotEqual(code, 0)
        self.assertIn("url_ieee", err)

    def test_plain_http_url_is_rejected_and_build_fails(self):
        bib = """
@article{evil2024f,
  title     = {A Normal Title},
  author    = {Normal, Author},
  journal   = {Journal of Testing},
  year      = {2024},
  url_arxiv = {http://arxiv.org/abs/1234.5678}
}
"""
        code, out, err, text = self._run_generator(bib)
        self.assertNotEqual(code, 0)
        self.assertIn("url_arxiv", err)

    def test_mixed_bib_one_hostile_entry_still_fails_whole_build(self):
        # A hostile entry anywhere in the file should reject the whole build
        # rather than silently emitting an unsafe link.
        bib = """
@article{good2024,
  title     = {A Fine Paper},
  author    = {Fine, Author},
  journal   = {Journal of Testing},
  year      = {2024},
  url_arxiv = {https://arxiv.org/abs/2501.09819}
}

@article{evil2024g,
  title   = {Another Paper},
  author  = {Another, Author},
  journal = {Journal of Testing},
  year    = {2024},
  url_pdf = {javascript:alert(1)}
}
"""
        code, out, err, text = self._run_generator(bib)
        self.assertNotEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
