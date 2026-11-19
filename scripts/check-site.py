#!/usr/bin/env python3
"""Check the rendered site in docs/ before pushing (standard library only).

Run it from anywhere after `quarto render`:

    python3 scripts/check-site.py              # check this repo
    python3 scripts/check-site.py OTHER_COPY   # check another copy of the repo

It only reads files (no web server). Each check prints PASS or FAIL with every
problem it found, and the script exits with status 1 if any check failed.
"""

import argparse
import difflib
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

SCRIPTS = Path(__file__).resolve().parent

# Ids Quarto itself writes twice on every page: one <link> for the dark theme and
# one for the light theme share the same id (Quarto 1.10 behaviour, harmless).
KNOWN_DUPLICATE_IDS = {"quarto-bootstrap", "quarto-text-highlighting-styles"}

# Files that must never be published, relative to docs/.
UNPUBLISHED = ["sources", "scripts", "connect.html", "publications-parsed.html",
               "publications.bib", "AGENTS.md", "README.md"]

# Which attributes of which tags point at a file. srcset is handled on its own.
URL_ATTRS = {
    "a": ["href"], "area": ["href"], "link": ["href"], "script": ["src"],
    "img": ["src"], "source": ["src"], "video": ["src", "poster"], "audio": ["src"],
    "track": ["src"], "iframe": ["src"], "embed": ["src"],
}
EXTERNAL_RE = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9+.-]*:|//)")  # https:, mailto:, data:, //cdn...
CSS_URL_RE = re.compile(r"""url\(\s*(['"]?)(.*?)\1\s*\)""")
DESCRIPTOR_RE = re.compile(r"\d+w|\d+(?:\.\d+)?x")
TEXT_SUFFIXES = {".html", ".css", ".js", ".json", ".xml", ".svg", ".qmd", ".yml", ".scss", ".txt"}


class Page(HTMLParser):
    """Everything the checks need from one HTML file, read in a single pass."""

    def __init__(self, path):
        super().__init__()
        self.path = path
        self.text = path.read_text(encoding="utf-8")
        self.elements = []  # (tag, attributes) for every start tag, in order
        self.css = []       # inline <style> blocks and style="" attributes
        self._in_style = False
        self.feed(self.text)
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = {name: value or "" for name, value in attrs}
        self.elements.append((tag, attrs))
        if "style" in attrs:
            self.css.append(attrs["style"])
        self._in_style = tag == "style"

    def handle_endtag(self, tag):
        if tag == "style":
            self._in_style = False

    def handle_data(self, data):
        if self._in_style:
            self.css.append(data)

    def ids(self):
        return [a["id"] for _, a in self.elements if "id" in a]


def srcset_urls(value):
    """Split a srcset into its URLs. Also return candidates that are not 'URL [100w|2x]'.

    A raw space inside a URL shows up as a bad candidate, because browsers split on spaces.
    """
    urls, bad = [], []
    for candidate in value.split(","):
        bits = candidate.split()
        if not bits:
            continue
        if len(bits) > 2 or (len(bits) == 2 and not DESCRIPTOR_RE.fullmatch(bits[1])):
            bad.append(candidate.strip())
        urls.append(bits[0])
    return urls, bad


def slugify(stem):
    """Folder name the gallery generator gives an image (same rule as in
    generate-gallery-derivatives.py): lower case, other characters become '-'."""
    return re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-") or "image"


def read_manifest_item(gallery, item):
    """Return (slug, caption, URLs) for one image in the gallery manifest.

    This is the ONLY place that knows the manifest's shape. If the gallery generator
    changes the manifest, adapt this function to build the same URLs as gallery.js.
    URLs are relative to the site root. Shape:
      {"caption", "slug", "width", "height", "thumbs": [400, ...], "mediums": [1200, ...]}
    with files thumb-<w>.avif/.webp, medium-<w>.webp and full-<width>.webp in
    assets/gallery-derivatives/<gallery>/<slug>/
    """
    folder = f"assets/gallery-derivatives/{gallery}/{item['slug']}"
    urls = [f"{folder}/full-{item['width']}.webp"]
    urls += [f"{folder}/thumb-{w}.{ext}" for w in item["thumbs"] for ext in ("avif", "webp")]
    urls += [f"{folder}/medium-{w}.webp" for w in item["mediums"]]
    return item["slug"], item.get("caption"), urls


class Site:
    """The repo copy being checked, with each HTML page parsed once."""

    def __init__(self, root):
        self.root = root
        self.docs = root / "docs"
        self.pages = {p: Page(p) for p in sorted(self.docs.glob("*.html"))}

    def rel(self, path):
        return path.relative_to(self.root).as_posix()

    def page(self, path):
        if path not in self.pages:
            self.pages[path] = Page(path)
        return self.pages[path]

    def check_url(self, url, base_dir, fragment_page=None):
        """Return a problem string if a local URL is broken, else None.

        fragment_page is the page a bare "#id" link points into; pass it only for
        <a>/<area> links, the only references whose #fragment the browser follows.
        """
        url = url.strip()
        if not url or EXTERNAL_RE.match(url):
            return None
        parts = urlsplit(url)
        path = unquote(parts.path)
        if not path:
            target = fragment_page
        else:
            target = (self.docs / path.lstrip("/")) if path.startswith("/") else (base_dir / path)
            target = target.resolve()
            if not target.is_relative_to(self.docs.resolve()):
                return f"{url} points outside docs/"
            if target.is_dir():
                target = target / "index.html"
            if not target.is_file():
                return f"{url} -> file not found"
        if parts.fragment and fragment_page and target and target.suffix == ".html":
            if unquote(parts.fragment) not in self.page(target).ids():
                return f"{url} -> no id #{parts.fragment} in {target.name}"
        return None


# ------------------------------------------------------------------ checks
# Each check takes the Site and returns a list of problems (empty list = PASS).

def check_references(site):
    """Every local href/src/srcset/poster and CSS url() resolves to a file (and #id)."""
    problems = []
    for path, page in site.pages.items():
        for tag, attrs in page.elements:
            follows_fragment = path if tag in ("a", "area") else None
            urls = [attrs[name] for name in URL_ATTRS.get(tag, ()) if name in attrs]
            urls += srcset_urls(attrs.get("srcset", ""))[0]
            for url in urls:
                if problem := site.check_url(url, path.parent, follows_fragment):
                    problems.append(f"{path.name}: <{tag}> {problem}")
        for css in page.css:
            for _, url in CSS_URL_RE.findall(css):
                if problem := site.check_url(url, path.parent):
                    problems.append(f"{path.name}: inline CSS url() {problem}")

    for css_file in sorted(site.docs.rglob("*.css")):
        for _, url in CSS_URL_RE.findall(css_file.read_text(encoding="utf-8")):
            if not url.startswith("#") and (problem := site.check_url(url, css_file.parent)):
                problems.append(f"{site.rel(css_file)}: url() {problem}")

    # The search box links straight to these hrefs, so they must resolve too.
    search = site.docs / "search.json"
    if search.exists():
        for item in json.loads(search.read_text(encoding="utf-8")):
            href = item.get("href", "")
            if problem := site.check_url(href, site.docs, site.docs / "index.html"):
                problems.append(f"search.json: {problem}")
    return problems


def check_srcset_spaces(site):
    """No srcset URL contains a raw space (pages and gallery manifest)."""
    problems = []
    for path, page in site.pages.items():
        for tag, attrs in page.elements:
            for bad in srcset_urls(attrs.get("srcset", ""))[1]:
                problems.append(f"{path.name}: <{tag}> bad srcset candidate {bad!r}")
    manifest = site.docs / "assets/gallery-derivatives/manifest.json"
    if manifest.exists():
        for bad in srcset_urls_in_json(json.loads(manifest.read_text(encoding="utf-8"))):
            problems.append(f"gallery manifest: bad srcset candidate {bad!r}")
    return problems


def srcset_urls_in_json(data):
    """Bad candidates in every string value under a key ending in 'srcset'."""
    if isinstance(data, dict):
        for key, value in data.items():
            if key.lower().endswith("srcset") and isinstance(value, str):
                yield from srcset_urls(value)[1]
            else:
                yield from srcset_urls_in_json(value)
    elif isinstance(data, list):
        for value in data:
            yield from srcset_urls_in_json(value)


def check_img_alt(site):
    """Every <img> has an alt attribute (alt="" is fine for decoration)."""
    return [f"{path.name}: <img src={a.get('src', '?')!r}> has no alt"
            for path, page in site.pages.items()
            for tag, a in page.elements if tag == "img" and "alt" not in a]


def check_blank_links(site):
    """Every target=_blank link has rel="noopener", so the new tab cannot control this one."""
    return [f"{path.name}: <{tag} href={a.get('href', '?')!r}> target=_blank without rel=noopener"
            for path, page in site.pages.items()
            for tag, a in page.elements
            if a.get("target") == "_blank" and "noopener" not in a.get("rel", "").split()]


def check_comments_and_fences(site):
    """HTML comments are closed and no Quarto fence text leaked into the page."""
    problems = []
    for path, page in site.pages.items():
        opened, closed = page.text.count("<!--"), page.text.count("-->")
        if opened != closed:
            problems.append(f"{path.name}: {opened} '<!--' but {closed} '-->'")
        if "{=html}" in page.text:
            problems.append(f"{path.name}: stray Quarto fence text '{{=html}}'")
    return problems


def check_duplicate_ids(site):
    """No id appears twice on a page (Quarto's own known pairs excepted)."""
    return [f"{path.name}: id {i!r} used {n} times"
            for path, page in site.pages.items()
            for i, n in Counter(page.ids()).items() if n > 1 and i not in KNOWN_DUPLICATE_IDS]


def check_media_dimensions(site):
    """Every <img>/<video> has width and height, so the page does not jump while loading."""
    # Markdown images sized with width=NN% cannot also carry width/height
    # attributes; they get a ratio-* class instead (aspect-ratio in the page CSS),
    # which reserves the same space.
    return [f"{path.name}: <{tag} src={a.get('src', '?')!r}> missing "
            + " and ".join(d for d in ("width", "height") if d not in a)
            for path, page in site.pages.items()
            for tag, a in page.elements
            if tag in ("img", "video") and not ("width" in a and "height" in a)
            and not any(c.startswith("ratio-") for c in a.get("class", "").split())]


def check_gallery(site):
    """Gallery manifest URLs exist, no derivative is unused, captions match gallery-content.json."""
    problems = []
    folder = site.docs / "assets/gallery-derivatives"
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    used = set()
    for gallery, items in manifest["galleries"].items():
        for item in items:
            for url in read_manifest_item(gallery, item)[2]:
                target = (site.docs / unquote(url)).resolve()
                used.add(target)
                if not target.is_file():
                    problems.append(f"{gallery}: {url} -> file not found")
    for file in sorted(folder.rglob("*")):
        if file.is_file() and file.name != "manifest.json" and file.resolve() not in used:
            problems.append(f"unreferenced derivative: {site.rel(file)}")

    # The generator copies captions from gallery-content.json into the manifest,
    # in the same order; each image's folder name (slug) comes from its file name.
    content = json.loads((site.root / "scripts/gallery-content.json").read_text(encoding="utf-8"))
    source_manifest = json.loads(
        (site.root / "assets/gallery-derivatives/manifest.json").read_text(encoding="utf-8"))
    for gallery, wanted in content["galleries"].items():
        have = [read_manifest_item(gallery, i) for i in source_manifest["galleries"].get(gallery, [])]
        if len(have) != len(wanted):
            problems.append(f"{gallery}: {len(wanted)} images in gallery-content.json, "
                            f"{len(have)} in the manifest")
        for want, (slug, caption, _) in zip(wanted, have):
            if slug != slugify(Path(want["file"]).stem):
                problems.append(f"{gallery}: order differs at {want['file']} (manifest has {slug})")
            elif caption != want["caption"]:
                problems.append(f"{gallery}: caption out of date for {want['file']}")
    if problems and any("caption" in p for p in problems):
        problems.append("fix: python3 scripts/generate-gallery-derivatives.py --captions-only")
    return problems


def check_publications(site):
    """publications-parsed.qmd is exactly what the parser makes from publications.bib."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "publications-parsed.qmd"
        run = subprocess.run(
            [sys.executable, str(SCRIPTS / "bib-to-quarto-parser.py"),
             "--bib", str(site.root / "publications.bib"), "-o", str(out)],
            capture_output=True, text=True)
        if run.returncode != 0:
            return [f"parser failed: {run.stderr.strip()}"]
        expected = out.read_text(encoding="utf-8")
    actual = (site.root / "publications-parsed.qmd").read_text(encoding="utf-8")
    if actual == expected:
        return []
    diff = difflib.unified_diff(actual.splitlines(), expected.splitlines(),
                                "publications-parsed.qmd (committed)", "parser output", lineterm="", n=0)
    return [line for line in list(diff)[:12]] + ["fix: python3 scripts/bib-to-quarto-parser.py"]


def check_assets_copied(site):
    """docs/ holds an identical copy of assets/ and cv/ (catches a missed render).

    Quarto copies these folders verbatim (`resources:` in _quarto.yml), so any
    difference means docs/ was not re-rendered after a file changed.
    """
    problems = []
    for folder in ("assets", "cv"):
        source, published = site.root / folder, site.docs / folder
        src = {p.relative_to(source) for p in source.rglob("*") if p.is_file()}
        pub = {p.relative_to(published) for p in published.rglob("*") if p.is_file()}
        problems += [f"{folder}/{p.as_posix()} not in docs/ (render needed)" for p in sorted(src - pub)]
        problems += [f"docs/{folder}/{p.as_posix()} has no source (stale output)" for p in sorted(pub - src)]
        problems += [f"docs/{folder}/{p.as_posix()} differs from its source (render needed)"
                     for p in sorted(src & pub)
                     if (source / p).read_bytes() != (published / p).read_bytes()]
    return problems


def image_metadata(path):
    """Names of metadata blocks (EXIF, XMP) found in one image file."""
    data = path.read_bytes()
    found = {"XMP"} if b"<x:xmpmeta" in data or b"<?xpacket" in data else set()
    suffix = path.suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        # Walk the JPEG segments up to the image data; EXIF lives in an APP1 segment.
        i = 2
        while i + 4 <= len(data) and data[i] == 0xFF and data[i + 1] not in (0xD9, 0xDA):
            length = int.from_bytes(data[i + 2:i + 4], "big")
            if data[i + 1] == 0xE1 and data[i + 4:i + 10] == b"Exif\0\0":
                found.add("EXIF")
            i += 2 + length
    elif suffix == ".png":
        # PNG chunks: 4-byte length, 4-byte type, data, 4-byte CRC.
        i = 8
        while i + 8 <= len(data):
            length, kind = int.from_bytes(data[i:i + 4], "big"), data[i + 4:i + 8]
            if kind == b"eXIf" or (kind in (b"tEXt", b"zTXt", b"iTXt")
                                   and b"exif" in data[i + 8:i + 40].lower()):
                found.add("EXIF")
            i += 12 + length
    elif suffix == ".webp":
        # RIFF chunks: 4-byte type, 4-byte little-endian length, data padded to even size.
        i = 12
        while i + 8 <= len(data):
            kind, length = data[i:i + 4], int.from_bytes(data[i + 4:i + 8], "little")
            if kind == b"EXIF":
                found.add("EXIF")
            i += 8 + length + (length & 1)
    elif suffix == ".avif":
        # The item list sits in the small 'meta' box near the start of the file.
        meta = data.find(b"meta")
        if meta != -1 and b"Exif" in data[meta:meta + 4096]:
            found.add("EXIF")
    return sorted(found)


def check_image_metadata(site):
    """No published image carries EXIF or XMP (GPS, camera serial, edit history)."""
    return [f"{site.rel(p)}: {', '.join(found)}"
            for p in sorted(site.docs.rglob("*"))
            if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".avif")
            and (found := image_metadata(p))]


def check_unpublished(site):
    """Private folders stay unpublished and no page or source points at them or at local disks."""
    problems = [f"docs/{name} is published but should not be"
                for name in UNPUBLISHED if (site.docs / name).exists()]
    # Files that end up on the site: page sources, styles, assets, and docs/ itself.
    files = [p for p in site.root.glob("*") if p.suffix in TEXT_SUFFIXES and p.name not in ("AGENTS.md", "README.md")]
    # Third-party code (Quarto's site_libs, vendored libraries) is skipped: it contains
    # these strings in its own code and is not something we edit.
    files += [p for folder in ("assets", "docs") for p in (site.root / folder).rglob("*")
              if p.suffix in TEXT_SUFFIXES and not {"site_libs", "vendor"} & set(p.parts)]
    pattern = re.compile(r"\bsources/|file://|/home/\w|/mnt/[a-z]/|\b[A-Z]:[\\/](?:Users|Hermes)")
    for path in sorted(files):
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in sorted({m.group() for m in pattern.finditer(text)}):
            problems.append(f"{site.rel(path)}: mentions {match!r}")
    return problems


CHECKS = [check_references, check_srcset_spaces, check_img_alt, check_blank_links,
          check_comments_and_fences, check_duplicate_ids, check_media_dimensions,
          check_gallery, check_publications, check_assets_copied, check_image_metadata,
          check_unpublished]


def main():
    parser = argparse.ArgumentParser(description="Check the rendered site in docs/.")
    parser.add_argument("root", nargs="?", type=Path, default=SCRIPTS.parent,
                        help="repo copy to check (default: this repo)")
    site = Site(parser.parse_args().root.resolve())
    if not site.pages:
        sys.exit(f"FAIL: no HTML pages in {site.docs} (run quarto render first)")

    failed = 0
    for check in CHECKS:
        try:
            problems = check(site)
        except Exception as exc:  # a crash in one check should not hide the others
            problems = [f"check crashed: {exc!r}"]
        name = check.__doc__.splitlines()[0]
        print(f"{'FAIL' if problems else 'PASS'}  {name}")
        for problem in problems:
            print(f"        {problem}")
        failed += bool(problems)
    print(f"\n{len(CHECKS) - failed} passed, {failed} failed ({len(site.pages)} pages in {site.docs})")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
