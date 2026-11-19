# Srivatsan Balaji - Portfolio

Personal academic website, live at <https://vatsan-b.github.io>. Built with
[Quarto](https://quarto.org) and hosted on GitHub Pages.

## Where things live

- `*.qmd` at the root: the pages (`_quarto.yml` lists which ones are built).
- `styles.css`, `custom-*.scss`: site styling and the dark and light themes.
- `assets/`: images, videos, gallery files and vendored libraries (all published).
- `publications.bib`: the publication list. `publications-parsed.qmd` is generated from it.
- `scripts/`: the site check and the generators (not published).
- `sources/`: original files kept out of the site (not published).
- `docs/`: the rendered site that GitHub Pages serves. Do not edit it by hand.

## Commands

Run from the repo root:

```sh
quarto render                                     # rebuild docs/ after any change
python3 scripts/check-site.py                     # check docs/ (links, images, gallery, publications)
python3 scripts/bib-to-quarto-parser.py           # after editing publications.bib
python3 scripts/generate-gallery-derivatives.py   # after changing gallery images or captions
```

Commit the sources together with the re-rendered `docs/`; pushing to `main` publishes the site.
See [AGENTS.md](AGENTS.md) for the full guide.

Developed with help from [Claude](https://claude.com/product/overview) and
[Codex](https://chatgpt.com/codex/). Currently managed by
[Hermes Agent](https://hermes-agent.nousresearch.com/).
