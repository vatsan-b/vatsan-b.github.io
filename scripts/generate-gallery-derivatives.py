#!/usr/bin/env python3
"""Generate justified-grid thumbnail and PhotoSwipe medium-resolution derivatives
for the for-fun.qmd galleries, plus the manifest gallery.js reads at runtime.

Reads scripts/gallery-content.json (source file + caption, hand-curated) and,
for each listed image, uses Pillow to emit:
  - preview (thumbnail) candidates in AVIF, WebP, and a JPEG fallback, at a
    fixed set of widths, for the justified-grid <picture> srcset.
  - medium candidates in WebP at a fixed set of widths, for PhotoSwipe's
    data-pswp-srcset. The untouched original is always the largest candidate.

Output is deterministic: same inputs (source bytes + gallery-content.json)
always produce byte-identical derivatives and manifest, so it's safe to
re-run. Output lives under assets/gallery-derivatives/, which is generated
and gitignored -- not committed.

Usage: python3 scripts/generate-gallery-derivatives.py
"""

import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageOps

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_PATH = REPO_ROOT / "scripts" / "gallery-content.json"
OUTPUT_DIR = REPO_ROOT / "assets" / "gallery-derivatives"
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"

THUMB_WIDTHS = (400, 800, 1200)
MEDIUM_WIDTHS = (1200, 1920)

WEBP_QUALITY = 82
WEBP_METHOD = 6
AVIF_QUALITY = 60
AVIF_SPEED = 6
FALLBACK_JPEG_QUALITY = 78

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(stem):
    slug = _SLUG_RE.sub("-", stem.lower()).strip("-")
    return slug or "image"


def load_source_image(path):
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)  # bake in orientation before dropping EXIF
    if img.mode != "RGB":
        img = img.convert("RGB")
    return img


def resized(img, width):
    if width >= img.width:
        return img
    height = round(img.height * (width / img.width))
    return img.resize((width, height), Image.LANCZOS)


def save_deterministic(img, path, fmt, **kwargs):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, fmt, **kwargs)


def relpath(path):
    return path.relative_to(REPO_ROOT).as_posix()


def build_item(gallery_key, entry):
    src_rel = entry["file"]
    src_path = REPO_ROOT / src_rel
    if not src_path.is_file():
        print(f"warning: skipping missing source {src_rel}", file=sys.stderr)
        return None

    slug = slugify(Path(src_rel).stem)
    out_dir = OUTPUT_DIR / gallery_key / slug

    img = load_source_image(src_path)
    orig_w, orig_h = img.width, img.height

    thumb_avif, thumb_webp, thumb_fallback = [], [], []
    for width in THUMB_WIDTHS:
        variant = resized(img, width)
        w = variant.width

        avif_path = out_dir / f"thumb-{w}.avif"
        save_deterministic(variant, avif_path, "AVIF", quality=AVIF_QUALITY, speed=AVIF_SPEED)
        thumb_avif.append((w, relpath(avif_path)))

        webp_path = out_dir / f"thumb-{w}.webp"
        save_deterministic(variant, webp_path, "WEBP", quality=WEBP_QUALITY, method=WEBP_METHOD)
        thumb_webp.append((w, relpath(webp_path)))

        jpg_path = out_dir / f"thumb-{w}.jpg"
        save_deterministic(variant, jpg_path, "JPEG", quality=FALLBACK_JPEG_QUALITY, optimize=True)
        thumb_fallback.append((w, relpath(jpg_path)))

        # thumbnail() never upscales; once a candidate matches the source
        # width there's no point emitting narrower duplicates beyond it.
        if w >= orig_w:
            break

    medium = []
    for width in MEDIUM_WIDTHS:
        if width >= orig_w:
            continue
        variant = resized(img, width)
        webp_path = out_dir / f"medium-{variant.width}.webp"
        save_deterministic(variant, webp_path, "WEBP", quality=WEBP_QUALITY, method=WEBP_METHOD)
        medium.append((variant.width, relpath(webp_path)))

    full_srcset_parts = [f"{url} {w}w" for w, url in medium]
    full_srcset_parts.append(f"{relpath(src_path)} {orig_w}w")

    return {
        "file": relpath(src_path),
        "caption": entry.get("caption", ""),
        "width": orig_w,
        "height": orig_h,
        "thumb": {
            "avifSrcset": ", ".join(f"{url} {w}w" for w, url in thumb_avif),
            "webpSrcset": ", ".join(f"{url} {w}w" for w, url in thumb_webp),
            "fallbackSrcset": ", ".join(f"{url} {w}w" for w, url in thumb_fallback),
            "fallbackSrc": thumb_fallback[len(thumb_fallback) // 2][1],
        },
        "full": {
            "srcset": ", ".join(full_srcset_parts),
            "src": relpath(src_path),
        },
    }


def main():
    content = json.loads(CONTENT_PATH.read_text())
    manifest = {"galleries": {}}

    for gallery_key, entries in content["galleries"].items():
        items = []
        for entry in entries:
            item = build_item(gallery_key, entry)
            if item is not None:
                items.append(item)
        manifest["galleries"][gallery_key] = items
        print(f"{gallery_key}: {len(items)} image(s) processed")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n")
    print(f"manifest written to {relpath(MANIFEST_PATH)}")


if __name__ == "__main__":
    main()
