#!/usr/bin/env python3
"""Regression tests for restoring ignored source media in a fresh clone."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "restore_source_assets.py"


def load_module():
    spec = spec_from_file_location("restore_source_assets", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {SCRIPT}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RestoreSourceAssetsTests(unittest.TestCase):
    def test_restores_missing_files_from_tracked_rendered_assets_without_overwriting(self):
        module = load_module()
        with TemporaryDirectory() as temporary_directory:
            repo = Path(temporary_directory)
            rendered = repo / "docs" / "assets" / "images"
            rendered.mkdir(parents=True)
            (rendered / "missing.png").write_bytes(b"rendered-copy")

            source = repo / "assets" / "images"
            source.mkdir(parents=True)
            (source / "keep.png").write_bytes(b"local-original")
            (rendered / "keep.png").write_bytes(b"rendered-old-copy")

            restored = module.restore_missing_assets(repo, asset_directories=("images",))

            self.assertEqual((source / "missing.png").read_bytes(), b"rendered-copy")
            self.assertEqual((source / "keep.png").read_bytes(), b"local-original")
            self.assertEqual(restored, [Path("assets/images/missing.png")])


if __name__ == "__main__":
    unittest.main()
