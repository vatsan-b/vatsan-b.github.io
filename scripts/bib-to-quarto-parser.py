#!/usr/bin/env python3
"""Generate publications-parsed.qmd from publications.bib, grouped by year (newest first).

No third-party dependencies — uses only the Python standard library.
"""

import re

BIB_PATH = "publications.bib"
OUT_PATH = "publications-parsed.qmd"

# Typed links, in display order. Label shown for each url_* field that is present.
LINKS = [
    ("url_ieee",  "IEEE Xplore"),
    ("url_doi",   "DOI"),
    ("url_arxiv", "arXiv preprint"),
    ("url_pdf",   "PDF"),
]


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
        return f'[{entry["status"]}]{{style="color: gray;"}}'

    venue = entry.get("booktitle") or entry.get("journal") or ""
    if "pages" in entry:
        pages = entry["pages"].replace("--", "–").replace("-", "–")
        venue += f" • Pages {pages}"
    return f"*{venue}*" if venue else ""


def links_line(entry):
    parts = [f'[{label}]({entry[key]})' + '{target="_blank"}'
             for key, label in LINKS if key in entry]
    if not parts:
        return ""
    return f'[{" • ".join(parts)}]{{style="color: gray;"}}'


def render_entry(entry):
    lines = [f'**{entry["title"]}**', author_line(entry)]
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
        out.append(render_entry(e) + "\n")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(out).lstrip() + "\n")

    print(f"Wrote {OUT_PATH} ({len(entries)} entries).")


if __name__ == "__main__":
    main()