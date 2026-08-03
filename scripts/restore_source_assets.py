#!/usr/bin/env python3
"""Restore ignored render inputs from the tracked Quarto output tree.

The canonical source directories are intentionally ignored to keep originals out
of Git, while their rendered copies in docs/assets are committed for deployment.
A fresh clone therefore needs this non-destructive bootstrap before Quarto reads
source media. Existing local files are never replaced.
"""

from __future__ import annotations

from pathlib import Path
from shutil import copy2
import sys


ASSET_DIRECTORIES = (
    "images",
    "videos",
    "unsplash-photos",
    "logos",
    "gallery-derivatives",
)


def restore_missing_assets(
    repository: Path, asset_directories: tuple[str, ...] = ASSET_DIRECTORIES
) -> list[Path]:
    """Copy only missing ignored source assets from tracked docs/assets."""
    restored: list[Path] = []
    for directory in asset_directories:
        rendered_root = repository / "docs" / "assets" / directory
        source_root = repository / "assets" / directory
        if not rendered_root.is_dir():
            continue

        for rendered_file in rendered_root.rglob("*"):
            if not rendered_file.is_file():
                continue
            relative_path = rendered_file.relative_to(rendered_root)
            source_file = source_root / relative_path
            if source_file.exists():
                continue
            source_file.parent.mkdir(parents=True, exist_ok=True)
            copy2(rendered_file, source_file)
            restored.append(source_file.relative_to(repository))
    return restored


def main() -> int:
    repository = Path(__file__).resolve().parent.parent
    restored = restore_missing_assets(repository)
    if restored:
        print(f"Restored {len(restored)} missing source asset(s) from docs/assets.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
