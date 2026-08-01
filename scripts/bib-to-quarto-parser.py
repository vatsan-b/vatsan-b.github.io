#!/usr/bin/env python3
"""Generate publications-parsed.qmd from publications.bib, grouped by year (newest first).

No third-party dependencies — uses only the Python standard library.
"""

import re
import sys
from urllib.parse import unquote

BIB_PATH = "publications.bib"
OUT_PATH = "publications-parsed.qmd"

# Typed links, in display order. Label shown for each url_* field that is present.
LINKS = [
    ("url_ieee",  "IEEE Xplore"),
    ("url_doi",   "DOI"),
    ("url_arxiv", "arXiv preprint"),
    ("url_pdf",   "PDF"),
]

# Strict allow-list for a `https://` URL: ASCII host (dotted labels), optional
# port, optional path/query/fragment drawn from a conservative RFC 3986-ish
# character set. Notably excludes "(", ")" and whitespace/control characters
# so a URL can never prematurely close a markdown `[label](url)` destination
# or smuggle raw HTML/markup into the rendered page.
_URL_RE = re.compile(
    r"^https://"
    r"(?P<host>[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+)"
    r"(?::[0-9]{1,5})?"
    r"(?P<path>/[A-Za-z0-9._~:/?#!$&'*+,;=%-]*)?$"
)
_PCT_BAD_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")


def escape_markdown(text):
    """Neutralize characters that could turn untrusted BibTeX field text into
    raw HTML or Quarto/Pandoc markup (tags, entities, links, spans, emphasis,
    code spans) once it lands in the generated .qmd file.
    """
    text = text.replace("\\", "\\\\")
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    for ch in "[]*_`":
        text = text.replace(ch, "\\" + ch)
    return text


def sanitize_url(raw, field, title):
    """Validate a url_* field value. Returns the URL unchanged if it is a
    well-formed https:// URL safe to embed in a markdown link destination;
    raises ValueError with a clear reason otherwise.
    """
    url = raw.strip()
    if not url:
        raise ValueError(f'{field} in "{title}": URL is empty')
    if url != raw:
        raise ValueError(f'{field} in "{title}": URL has leading/trailing whitespace')
    if any(ord(c) < 0x20 or c == "\x7f" for c in url):
        raise ValueError(f'{field} in "{title}": URL contains control characters')
    if _PCT_BAD_RE.search(url):
        raise ValueError(f'{field} in "{title}": URL has malformed percent-encoding')
    if any(ord(c) < 0x20 or c == "\x7f" for c in unquote(url)):
        raise ValueError(f'{field} in "{title}": URL percent-encodes a control character')
    if not _URL_RE.match(url):
        raise ValueError(f'{field} in "{title}": not a well-formed https:// URL: {url!r}')
    return url


def parse_bib(text):
    """Minimal BibTeX parser. Returns a list of {field: value} dicts (fields lowercased).

    Handles brace-delimited values with nesting (e.g. titles containing {LaTeX}),
    quote-delimited values, multi-line values, and % line comments.
    """
    # strip whole-line comments
    text = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("%"))

    entries = []
    i = 0
    while True:
        at = text.find("@", i)
        if at == -1:
            break
        brace = text.find("{", at)
        if brace == -1:
            break

        # walk to the matching close brace for the whole entry
        depth, j = 0, brace
        while j < len(text):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        body = text[brace + 1:j]
        i = j + 1

        # drop the citation key (everything up to the first comma)
        comma = body.find(",")
        fields_str = body[comma + 1:] if comma != -1 else ""

        entry = {}
        k = 0
        while k < len(fields_str):
            eq = fields_str.find("=", k)
            if eq == -1:
                break
            name = fields_str[k:eq].strip().lower()
            v = eq + 1
            while v < len(fields_str) and fields_str[v].isspace():
                v += 1
            if v >= len(fields_str):
                break

            if fields_str[v] == "{":
                d, end = 0, v
                while end < len(fields_str):
                    if fields_str[end] == "{":
                        d += 1
                    elif fields_str[end] == "}":
                        d -= 1
                        if d == 0:
                            break
                    end += 1
                value = fields_str[v + 1:end]
                k = end + 1
            elif fields_str[v] == '"':
                end = fields_str.find('"', v + 1)
                value = fields_str[v + 1:end]
                k = end + 1
            else:  # bare value (e.g. a year not in braces)
                end = v
                while end < len(fields_str) and fields_str[end] not in ",\n":
                    end += 1
                value = fields_str[v:end].strip()
                k = end + 1

            # skip past a trailing comma
            while k < len(fields_str) and fields_str[k] in ", \n\t":
                k += 1
            if name:
                entry[name] = re.sub(r"\s+", " ", value).strip()

        if entry:
            entries.append(entry)
    return entries


def fmt_author(raw):

    raw = raw.strip()
    if "," in raw:
        last, first = (p.strip() for p in raw.split(",", 1))
    else:
        parts = raw.split()
        last, first = parts[-1], " ".join(parts[:-1])
    initials = " ".join(tok[0] + "." for tok in first.replace(".", " ").split() if tok)
    return f"{last}, {initials}".rstrip(", ").strip()


def author_line(entry):
    raw_authors = [a.strip() for a in entry["author"].split(" and ")]
    cofirst = {n.strip().lower() for n in entry.get("cofirst", "").split(" and ") if n.strip()}

    names = []
    for raw in raw_authors:
        formatted = fmt_author(raw)
        last = formatted.split(",")[0].strip().lower()
        formatted = escape_markdown(formatted)
        if last in cofirst:
            formatted += r"\*"  # literal asterisk after the name
        names.append(formatted)

    line = ", ".join(names)
    if cofirst:
        line += r" • \**Co-first Authors*"
    return line


def venue_line(entry):
    """Italic venue (+ pages), or the gray status line if `status` is set."""
    if "status" in entry:
        return f'[{escape_markdown(entry["status"])}]{{style="color: gray;"}}'

    venue = entry.get("booktitle") or entry.get("journal") or ""
    if "pages" in entry:
        pages = entry["pages"].replace("--", "–").replace("-", "–")
        venue += f" • Pages {pages}"
    venue = escape_markdown(venue)
    return f"*{venue}*" if venue else ""


def links_line(entry):
    title = entry.get("title", "<untitled>")
    parts = []
    for key, label in LINKS:
        if key not in entry:
            continue
        url = sanitize_url(entry[key], key, title)
        parts.append(f'[{label}]({url})' + '{target="_blank"}')
    if not parts:
        return ""
    return f'[{" • ".join(parts)}]{{style="color: gray;"}}'


def render_entry(entry):
    lines = [f'**{escape_markdown(entry["title"])}**', author_line(entry)]
    v = venue_line(entry)
    if v:
        lines.append(v)
    links = links_line(entry)
    if links:
        lines.append(links)
    # join with Quarto hard line breaks ("\" + newline), no trailing break on last line
    return "\\\n".join(lines)


def main():
    with open(BIB_PATH, encoding="utf-8") as f:
        entries = parse_bib(f.read())

    # newest year first; stable, so within-year order follows the .bib file
    entries.sort(key=lambda e: int(e["year"]), reverse=True)

    out = []
    current_year = None
    for e in entries:
        if e["year"] != current_year:
            current_year = e["year"]
            out.append(f"\n## {current_year}\n")
        try:
            out.append(render_entry(e) + "\n")
        except ValueError as exc:
            sys.exit(f"error: rejected entry: {exc}")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(out).lstrip() + "\n")

    print(f"Wrote {OUT_PATH} ({len(entries)} entries).")


if __name__ == "__main__":
    main()