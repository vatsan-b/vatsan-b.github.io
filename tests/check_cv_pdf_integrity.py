#!/usr/bin/env python3
"""Regression check: the published CV must have a usable PDF cross-reference."""
from pathlib import Path


def assert_pdf_cross_reference(path: Path) -> None:
    pdf = path.read_bytes()
    assert pdf.startswith(b"%PDF-"), f"{path}: missing PDF header"
    try:
        offset = int(pdf.rsplit(b"startxref", 1)[1].splitlines()[1])
    except (IndexError, ValueError) as exc:
        raise AssertionError(f"{path}: missing or malformed startxref") from exc
    assert pdf[offset : offset + 32].startswith((b"xref", b"6 0 obj", b"1 0 obj")), (
        f"{path}: startxref={offset} does not point to a cross-reference section; "
        f"found {pdf[offset : offset + 32]!r}"
    )


if __name__ == "__main__":
    for pdf in (Path("cv/CV_SrivatsanBalaji.pdf"), Path("docs/cv/CV_SrivatsanBalaji.pdf")):
        assert_pdf_cross_reference(pdf)
    print("PASS")
