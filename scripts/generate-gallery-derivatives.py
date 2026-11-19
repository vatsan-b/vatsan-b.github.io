#!/usr/bin/env python3
"""Build the Leisure page (for-fun.qmd) gallery images and their manifest.

Reads scripts/gallery-content.json (hand-edited: source file and caption per
image, in display order) and writes, per image, into
assets/gallery-derivatives/<gallery>/<slug>/:
  thumb-<w>.avif, thumb-<w>.webp   grid thumbnails (400/800/1200 px wide)
  medium-<w>.webp                  lightbox sizes (1200/1920 px wide)
  full-<w>.webp                    largest lightbox size, long edge <= 2560 px
plus assets/gallery-derivatives/manifest.json, which gallery.js reads. The
manifest stores only what cannot be worked out from the file-name pattern
above; gallery.js builds the URLs. It does not name the source files, so the
published site never shows the original file names or the sources/ folder.

The originals stay in sources/gallery-originals/, which is not published,
because some carry GPS or camera-serial metadata. Derivatives carry none.

Existing files are kept as they are, so a normal run only encodes new images
(use --force after replacing a source image under the same name). Files that
the manifest no longer lists are deleted.

Usage:
  python3 scripts/generate-gallery-derivatives.py                  # build what is missing (needs Pillow)
  python3 scripts/generate-gallery-derivatives.py --force          # re-encode everything
  python3 scripts/generate-gallery-derivatives.py --captions-only  # copy captions into the manifest
                                                                   # (no Pillow, no image work)
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_PATH = REPO_ROOT / "scripts" / "gallery-content.json"  # hand-edited input
OUTPUT_DIR = REPO_ROOT / "assets" / "gallery-derivatives"      # published output
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"                   # read by gallery.js

THUMB_WIDTHS = (400, 800, 1200)   # grid thumbnail widths (never wider than the source)
MEDIUM_WIDTHS = (1200, 1920)      # lightbox widths (only those narrower than the full size)
FULL_MAX_EDGE = 2560              # long edge cap of the largest published size

# Encoder settings. Changing them only affects files written from now on;
# run with --force to re-encode the existing ones.
AVIF = {"quality": 60, "speed": 6}
WEBP = {"quality": 82, "method": 6}
FULL_WEBP = {"quality": 85, "method": 6}


def slugify(stem):
    """Folder name for an image: lower case, runs of other characters become '-'."""
    return re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-") or "image"


def fail(message):
    sys.exit(f"error: {message}")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_manifest(manifest):
    """One image per line: small, readable diffs. LF endings even on Windows."""
    lines = ["{", '  "galleries": {']
    galleries = list(manifest["galleries"].items())
    for g, (key, items) in enumerate(galleries):
        lines.append(f"    {json.dumps(key)}: [")
        for i, item in enumerate(items):
            comma = "," if i < len(items) - 1 else ""
            lines.append(f"      {json.dumps(item)}{comma}")
        lines.append("    ]" + ("," if g < len(galleries) - 1 else ""))
    lines += ["  }", "}", ""]
    MANIFEST_PATH.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def captions_only(content):
    """Copy edited captions from gallery-content.json into the existing manifest.

    Entries are matched in order; each one's folder name (slug) must still match
    its file name, otherwise images were added, removed or reordered and a full
    run is needed."""
    manifest = read_json(MANIFEST_PATH)
    changed = 0
    for key, items in manifest["galleries"].items():
        entries = content["galleries"].get(key, [])
        slugs = [slugify(Path(e["file"]).stem) for e in entries]
        if slugs != [item["slug"] for item in items]:
            fail(f"'{key}' images were added, removed or reordered; run without --captions-only")
        for entry, item in zip(entries, items):
            caption = entry.get("caption", "")
            if item["caption"] != caption:
                item["caption"] = caption
                changed += 1
    write_manifest(manifest)
    print(f"manifest captions updated ({changed} changed)")


def build_image(gallery, slug, entry, force):
    """Write the missing derivatives for one image; return its manifest entry
    and the set of files it owns."""
    from PIL import Image, ImageOps  # imported here so --captions-only needs no Pillow

    source = REPO_ROOT / entry["file"]
    if not source.is_file():
        fail(f"source image not found: {entry['file']}")
    folder = OUTPUT_DIR / gallery / slug

    img = ImageOps.exif_transpose(Image.open(source))  # apply rotation before metadata is dropped
    img = img.convert("RGB")

    # Largest published size: the source scaled down to FULL_MAX_EDGE, never up.
    scale = min(1, FULL_MAX_EDGE / max(img.size))
    full_w, full_h = round(img.width * scale), round(img.height * scale)

    # A thumbnail is never wider than the source; stop at the first one that reaches it.
    thumbs = []
    for w in THUMB_WIDTHS:
        thumbs.append(min(w, img.width))
        if w >= img.width:
            break
    mediums = [w for w in MEDIUM_WIDTHS if w < full_w]

    def size_for(width):
        return (width, round(img.height * (width / img.width)))

    # (file name, pixel size, Pillow format, encoder options)
    outputs = [(f"full-{full_w}.webp", (full_w, full_h), "WEBP", FULL_WEBP)]
    for w in thumbs:
        outputs.append((f"thumb-{w}.avif", size_for(w), "AVIF", AVIF))
        outputs.append((f"thumb-{w}.webp", size_for(w), "WEBP", WEBP))
    outputs += [(f"medium-{w}.webp", size_for(w), "WEBP", WEBP) for w in mediums]

    folder.mkdir(parents=True, exist_ok=True)
    for name, size, fmt, options in outputs:
        path = folder / name
        if path.exists() and not force:
            continue
        Image.init()  # registers every format this Pillow can write
        if fmt not in Image.SAVE:
            fail(f"this Pillow cannot write {fmt}, needed for {path.name}; see scripts/requirements.txt")
        variant = img if size == img.size else img.resize(size, Image.LANCZOS)
        variant.save(path, fmt, **options)  # no exif/xmp passed, so none is written

    item = {
        "caption": entry.get("caption", ""),
        "slug": slug,
        "width": full_w,        # size of full-<width>.webp
        "height": full_h,
        "thumbs": thumbs,
        "mediums": mediums,
    }
    return item, {folder / name for name, *_ in outputs}


def remove_unlisted(keep):
    """Delete derivative files and folders that the manifest no longer lists."""
    keep = keep | {MANIFEST_PATH}
    for path in sorted(OUTPUT_DIR.rglob("*"), reverse=True):  # children before parents
        if path.is_file() and path not in keep:
            print(f"removed {path.relative_to(REPO_ROOT).as_posix()}")
            path.unlink()
        elif path.is_dir() and not any(path.iterdir()):
            path.rmdir()


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--force", action="store_true", help="re-encode files that already exist")
    parser.add_argument("--captions-only", action="store_true",
                        help="only copy captions into the existing manifest (no Pillow needed)")
    args = parser.parse_args()

    content = read_json(CONTENT_PATH)
    if args.captions_only:
        captions_only(content)
        return

    manifest = {"galleries": {}}
    keep = set()
    for gallery, entries in content["galleries"].items():
        items = []
        for entry in entries:
            slug = slugify(Path(entry["file"]).stem)
            if any(other["slug"] == slug for other in items):
                fail(f"two images in '{gallery}' share the folder name '{slug}'; rename one source file")
            item, files = build_image(gallery, slug, entry, args.force)
            items.append(item)
            keep |= files
        manifest["galleries"][gallery] = items
        print(f"{gallery}: {len(items)} image(s)")

    write_manifest(manifest)
    remove_unlisted(keep)
    print(f"manifest written to {MANIFEST_PATH.relative_to(REPO_ROOT).as_posix()}")


if __name__ == "__main__":
    main()
