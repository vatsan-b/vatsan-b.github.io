#!/usr/bin/env python3
"""Build publications-parsed.qmd from publications.bib (standard library only).

publications.qmd includes the generated file, so edit the .bib and re-run this
script; never edit publications-parsed.qmd by hand.

    python3 scripts/bib-to-quarto-parser.py              # rewrite publications-parsed.qmd
    python3 scripts/bib-to-quarto-parser.py -o out.qmd   # write somewhere else

Any problem in the .bib (unclosed brace or quote, missing field, bad URL)
stops the script with a message naming the entry, so nothing is dropped silently.
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote

REPO = Path(__file__).resolve().parent.parent

# Typed links, in display order: (bib field, label shown on the page).
LINKS = [
    ("url_ieee", "IEEE Xplore"),
    ("url_doi", "DOI"),
    ("url_arxiv", "arXiv preprint"),
    ("url_pdf", "PDF"),
]

# A plain https:// URL. "(", ")" and whitespace are not allowed, so a URL can
# never end the markdown [label](url) early or slip markup into the page.
URL_RE = re.compile(
    r"^https://"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+"
    r"(?::[0-9]{1,5})?"
    r"(?:/[A-Za-z0-9._~:/?#!$&'*+,;=%-]*)?$"
)
BAD_PERCENT_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")

# LaTeX accent commands -> Unicode combining marks, e.g. \'e -> é, \c{c} -> ç.
ACCENTS = {
    "'": "\u0301", "`": "\u0300", "^": "\u0302", '"': "\u0308", "~": "\u0303",
    "=": "\u0304", ".": "\u0307", "u": "\u0306", "v": "\u030c", "H": "\u030b",
    "c": "\u0327", "k": "\u0328", "r": "\u030a", "d": "\u0323", "b": "\u0331",
}
# Punctuation accents attach directly (\'e); letter accents need a brace or space (\c{c}, \c c).
# The base letter may be \i or \j (dotless i/j), as in \'{\i}.
ACCENT_RE = re.compile(
    r"""\\(?:([`'^"~=.])|([uvHckrdb])(?=[\s{]))\s*(?:\{\s*(\\?[A-Za-z])\s*\}|(\\?[A-Za-z]))"""
)
# Letter-like commands, e.g. {\o}rsted -> ørsted. LaTeX swallows one space after them.
SYMBOLS = {
    "ss": "ß", "ae": "æ", "AE": "Æ", "oe": "œ", "OE": "Œ", "aa": "å", "AA": "Å",
    "o": "ø", "O": "Ø", "l": "ł", "L": "Ł", "i": "ı", "j": "ȷ",
}
SYMBOL_RE = re.compile(r"\\(ss|ae|AE|oe|OE|aa|AA|o|O|l|L|i|j)(?![A-Za-z])(?:\{\}| )?")
ESCAPED_RE = re.compile(r"\\([&%$#_])")  # \& -> &, \% -> %, ...


class BibError(Exception):
    """A problem in publications.bib, reported to the user and stops the script."""


# ---------------------------------------------------------------- text helpers

def latex_to_unicode(text):
    """Turn common LaTeX accents and symbols into plain Unicode characters.

    Unknown commands are left alone (escape_markdown then shows the backslash).
    """
    def accent(m):
        base = (m.group(3) or m.group(4)).lstrip("\\")
        return unicodedata.normalize("NFC", base + ACCENTS[m.group(1) or m.group(2)])

    text = ACCENT_RE.sub(accent, text)
    text = SYMBOL_RE.sub(lambda m: SYMBOLS[m.group(1)], text)
    return ESCAPED_RE.sub(r"\1", text)


def escape_markdown(text):
    """Make .bib text safe to drop into the .qmd: no raw HTML or markdown syntax."""
    text = text.replace("\\", "\\\\")
    text = text.replace("{", "").replace("}", "")  # BibTeX case-protection braces
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    for ch in "[]*_`$@":
        text = text.replace(ch, "\\" + ch)
    return text


def matching_brace(text, start):
    """Index of the "}" that closes the "{" at text[start], or -1 if never closed."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1


def split_outside_braces(text, separator):
    """Split on a regex separator (any letter case), except inside {...}.

    Braces protect text in BibTeX: "{Barnes and Noble} and Smith, J." is two names.
    """
    parts, depth, start = [], 0, 0
    for m in re.finditer(r"[{}]|" + separator, text, flags=re.IGNORECASE):
        if m.group() == "{":
            depth += 1
        elif m.group() == "}":
            depth -= 1
        elif depth == 0:
            parts.append(text[start:m.start()])
            start = m.end()
    parts.append(text[start:])
    return [p.strip() for p in parts if p.strip()]


# ---------------------------------------------------------------- .bib parsing

def parse_bib(text):
    """Return a list of (label, fields) for every entry, in file order.

    label names the entry for error messages, e.g. "@inproceedings{good2024} (line 12)".
    fields maps lowercase field names to values with whitespace collapsed.
    """
    # Blank out % comment lines but keep the line count, so line numbers stay right.
    text = "\n".join("" if line.lstrip().startswith("%") else line for line in text.splitlines())

    entries, seen_keys, pos = [], set(), 0
    while (at := text.find("@", pos)) != -1:
        line = text.count("\n", 0, at) + 1
        brace = text.find("{", at)
        kind = text[at + 1:brace].strip().lower() if brace != -1 else ""
        if not re.fullmatch(r"[a-z]+", kind):
            raise BibError(f"line {line}: stray '@' that does not start an entry like @article{{...}}")
        close = matching_brace(text, brace)
        if close == -1:
            raise BibError(f"line {line}: @{kind} entry is never closed (unbalanced braces)")
        pos = close + 1
        if kind in ("string", "comment", "preamble"):
            continue  # not publications

        key, _, body = text[brace + 1:close].partition(",")
        key = key.strip()
        label = f"@{kind}{{{key}}} (line {line})"
        if key in seen_keys:
            raise BibError(f"{label}: citation key used twice")
        seen_keys.add(key)
        try:
            fields = parse_fields(body)
        except BibError as exc:
            raise BibError(f"{label}: {exc}") from None
        if not fields:
            raise BibError(f"{label}: no fields found")
        entries.append((label, fields))
    return entries


def parse_fields(body):
    """Parse 'name = {value}, name = "value", name = 2024' into a dict."""
    fields, k = {}, 0
    while True:
        while k < len(body) and (body[k].isspace() or body[k] == ","):
            k += 1
        if k >= len(body):
            return fields

        eq = body.find("=", k)
        if eq == -1:
            raise BibError(f"unexpected text {body[k:k + 30].strip()!r} (missing '=')")
        name = body[k:eq].strip().lower()
        if not re.fullmatch(r"[a-z0-9_:.+-]+", name):
            raise BibError(f"bad field name {name!r} (missing comma before it?)")
        if name in fields:
            raise BibError(f"field {name!r} given twice")

        v = eq + 1
        while v < len(body) and body[v].isspace():
            v += 1
        if v >= len(body):
            raise BibError(f"field {name!r} has no value")
        if body[v] == "{":
            end = matching_brace(body, v)
            if end == -1:
                raise BibError(f"field {name!r}: '{{' is never closed")
            value, k = body[v + 1:end], end + 1
        elif body[v] == '"':
            end = body.find('"', v + 1)
            if end == -1:
                raise BibError(f"field {name!r}: opening '\"' is never closed")
            value, k = body[v + 1:end], end + 1
        else:  # bare value such as year = 2024
            end = re.compile(r"[^,\n]*").match(body, v).end()
            value, k = body[v:end], end

        # Only whitespace may sit between a value and the next comma.
        rest = body[k:].lstrip()
        if rest and rest[0] != ",":
            raise BibError(f"field {name!r}: unexpected text after the value (missing comma?)")

        value = re.sub(r"\s+", " ", value).strip()
        fields[name] = value if name.startswith("url") else latex_to_unicode(value)


# ---------------------------------------------------------------- rendering

def sanitize_url(raw, field):
    """Return raw if it is a well-formed https:// URL, else raise BibError."""
    url = raw.strip()
    if not url:
        raise BibError(f"{field}: URL is empty")
    if any(ord(c) < 0x20 or c == "\x7f" for c in unquote(url)):
        raise BibError(f"{field}: URL contains control characters")
    if BAD_PERCENT_RE.search(url):
        raise BibError(f"{field}: URL has malformed percent-encoding")
    if not URL_RE.match(url):
        raise BibError(f"{field}: not a well-formed https:// URL: {url!r}")
    return url


def format_author(name):
    """'Lipton, Jeffrey I.' or 'Jeffrey I. Lipton' -> 'Lipton, J. I.'.

    A name wrapped in braces, like {OpenAI Robotics}, is shown as written.
    """
    if name.startswith("{") and matching_brace(name, 0) == len(name) - 1:
        return name[1:-1]
    parts = split_outside_braces(name, r",")
    if len(parts) > 1:
        last, first = parts[0], ", ".join(parts[1:])
    else:
        words = split_outside_braces(name, r"\s+")
        last, first = words[-1], " ".join(words[:-1])
    # Hyphenated given names keep both initials: "Jean-Paul" -> "J.-P."
    given = [w.replace("{", "").replace("}", "") for w in first.replace(".", " ").split()]
    initials = " ".join(
        "-".join(part[0] + "." for part in word.split("-") if part) for word in given if word
    )
    return f"{last}, {initials}".rstrip(", ").strip()


def author_line(entry):
    """Author list; co-first authors get a "*" and a note at the end."""
    cofirst = {n.replace("{", "").replace("}", "").lower()
               for n in split_outside_braces(entry.get("cofirst", ""), r"\s+and\s+")}
    names = []
    for raw in split_outside_braces(entry["author"], r"\s+and\s+"):
        formatted = format_author(raw)
        last = formatted.split(",")[0].replace("{", "").replace("}", "").strip().lower()
        formatted = escape_markdown(formatted)
        if last in cofirst:
            formatted += r"\*"  # literal asterisk after the name
        names.append(formatted)
    line = ", ".join(names)
    if cofirst:
        line += r" • [\*Co-first Authors]{.cofirst-note}"
    return line


def venue_line(entry):
    """Venue (+ pages) in .publication-venue, or the grey status line if `status` is set."""
    if "status" in entry:
        return f'[{escape_markdown(entry["status"])}]{{style="color: gray;"}}'
    venue = entry.get("booktitle") or entry.get("journal") or ""
    if "pages" in entry:
        pages = entry["pages"].replace("--", "–").replace("-", "–")
        venue += f" • Pages {pages}"
    venue = escape_markdown(venue)
    return f"[{venue}]{{.publication-venue}}" if venue else ""


def links_line(entry):
    """Grey row of typed links. They open in a new tab, with rel=noopener for safety."""
    parts = [
        f"[{label}]({sanitize_url(entry[field], field)})" + '{target="_blank" rel="noopener"}'
        for field, label in LINKS
        if field in entry
    ]
    return f'[{" • ".join(parts)}]{{style="color: gray;"}}' if parts else ""


def render_entry(entry):
    """One publication: title, authors, venue, links, joined by Quarto hard line breaks."""
    lines = [escape_markdown(entry["title"]), f"[{author_line(entry)}]{{.publication-authors}}"]
    lines += [line for line in (venue_line(entry), links_line(entry)) if line]
    return "\\\n".join(lines)


def build(bib_text):
    """Return the full .qmd text and the number of publications."""
    entries = parse_bib(bib_text)
    if not entries:
        raise BibError("no entries found")
    for label, entry in entries:
        missing = [f for f in ("title", "author", "year") if not entry.get(f)]
        if missing:
            raise BibError(f"{label}: missing {', '.join(missing)}")
        if not entry["year"].isdigit():
            raise BibError(f"{label}: year is not a number: {entry['year']!r}")

    # Newest year first. sort() is stable, so within a year the .bib order is kept.
    entries.sort(key=lambda item: int(item[1]["year"]), reverse=True)
    blocks = []
    for label, entry in entries:
        try:
            blocks.append(render_entry(entry) + "\n")
        except BibError as exc:
            raise BibError(f"{label}: {exc}") from None
    return "\n".join(blocks) + "\n", len(entries)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bib", type=Path, default=REPO / "publications.bib", help="input .bib file")
    parser.add_argument("-o", "--output", type=Path, default=REPO / "publications-parsed.qmd",
                        help="output .qmd file (default: publications-parsed.qmd in the repo)")
    args = parser.parse_args()

    try:
        qmd, count = build(args.bib.read_text(encoding="utf-8"))
    except OSError as exc:
        sys.exit(f"error: cannot read {args.bib}: {exc.strerror}")
    except BibError as exc:
        sys.exit(f"error in {args.bib.name}: {exc}")
    args.output.write_text(qmd, encoding="utf-8", newline="\n")
    print(f"Wrote {args.output} ({count} entries).")


if __name__ == "__main__":
    main()
