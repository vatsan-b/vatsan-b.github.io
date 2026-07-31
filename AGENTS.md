# vatsan-b.github.io — Personal Website

Personal academic site for Srivatsan Balaji. Static site built with **Quarto**.

- **v1** — live at <https://vatsan-b.github.io>, served from `main`.
- **v2** — in progress on the `sandbox` branch. Different build from v1; not yet merged.

## Build layout — read this before deleting anything

Sources live at the repo root as `.qmd` files. `quarto render` compiles them into
`docs/`, and **GitHub Pages serves the site from `docs/`**. Both the sources and the
rendered output are committed.

This means `docs/assets/`, `docs/site_libs/`, `docs/_extensions/`, and `docs/*.html`
duplicate files that also exist at the repo root. **That duplication is correct Quarto
behaviour, not cruft.** Deleting `docs/` or its contents takes the live site down.

Genuine cruft — `docs.bak/` and any nested variant — was removed in commit `accbefb`
and is now covered by `.gitignore` (`*.bak/`, `docs.bak/`).

## Pages (v2 / sandbox)

| Source | Page |
|---|---|
| `index.qmd` | Landing + about. Three.js WebGL hero (wave-grid of deforming unit cells, shader tuned via a `CFG` block; auxetic/torsion theme mirrors the research). Respects `prefers-reduced-motion`. |
| `research.qmd` | Five project write-ups, each with figure or video, funding note, and IEEE/arXiv links. |
| `publications.qmd` | See generation note below. |
| `mentoring.qmd` | Mentee list. |
| `for-fun.qmd` | Flight-sim and photography galleries (flickr-justified-gallery + lightGallery). |

## Publications are generated — do not hand-edit

`publications-parsed.qmd` is produced from `publications.bib` by
`scripts/bib-to-quarto-parser.py`. Edit the `.bib` and re-run the script; edits made
directly to the parsed `.qmd` are overwritten on the next run.

## Assets

Source assets in `assets/images/`, `assets/videos/`, `assets/unsplash-photos/`, and
`assets/logos/` are **gitignored and untracked** (untracked in `accbefb`; the files
remain on disk locally). Consequence: a fresh clone cannot fully `quarto render` —
the rendered `docs/assets/` in git is the only committed copy of those images.

`assets/flight-sim/` **is** tracked. `assets/compress-photo.py` is source code, also tracked.

## Conventions

- Body copy is justified via a page-level `<style>` block; centred figure/video divs
  override it by inheritance. Do not target `main p` — Quarto wraps figure images in
  `<p>` and it drags images left.
- Research and for-fun pages use a right-hand TOC with short sidebar labels supplied by
  `{toc-text="..."}` on each heading, rewritten client-side by a script at the bottom of
  `research.qmd`.
- External links carry `target="_blank"`.
- Dark theme throughout; accent colour `#FDD26E`.

## Open items

- Bio does not mention the Nimble Surgical role.
- `maintenance.html` sits at the repo root, purpose unconfirmed. It was previously in
  `.gitignore`; that entry was removed and the file is now tracked deliberately.
- `docs/connect.html` exists in the build output but has **no** `connect.qmd` source in
  `sandbox` — it is v1 leftover and will vanish on a clean render.
- Quarto is **not installed** on the VM, so the site cannot be rebuilt here yet.

## Git

- Work happens on `sandbox`. `main` holds v1 and is currently at `ebd10e5c`.
- Never force-push. Never push to `main` without explicit instruction.
- Old blobs from the removed `docs.bak/` trees still sit in history, so `.git` is ~72 MB
  despite the working tree being ~146 MB. Shrinking it needs `git filter-repo` and a
  force-push — destructive, rewrites every SHA. Do not do this unprompted.
