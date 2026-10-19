# vatsan-b.github.io — Personal Website

Personal academic site for Srivatsan. Static site built with **Quarto** (1.10.18 installed locally as `quarto` on `PATH`).

- **Current site** — live at <https://vatsan-b.github.io>, served from `main`.

## Build layout — read this before deleting anything

Sources live at the repo root as `.qmd` files. `quarto render` compiles them into
`docs/`, and **GitHub Pages serves the site from `docs/`**. Both the sources and the
rendered output are committed.

This means `docs/assets/`, `docs/site_libs/` and `docs/*.html` duplicate files that
also exist at the repo root. **That duplication is correct Quarto behaviour, not
cruft.** Deleting `docs/` or its contents takes the live site down. Rendered output is
committed, so review generated-library changes when the renderer version changes.

Genuine cruft — `docs.bak/` and any nested variant — was removed in commit `da8c3e6`
and remains covered by the `*.bak/` ignore rule. `temp/` and `.quarto/` are gitignored
(`.gitignore`) scratch space; keep probe files in `temp/` and delete them when done.

## Pages

`_quarto.yml` renders exactly six pages, in navbar order.

| Source | Page |
|---|---|
| `index.qmd` | Home. Two-column hero: headline and intro text on the left, a muted looping Formlabs SLA timelapse (`assets/videos/formlabs-sla-hsa.mp4`) with a soft radial glow on the right. The video plays only while on screen and never under `prefers-reduced-motion`. The headline is a styled `div role="heading"`, not an `<h1>`, because Quarto lifts an `<h1>` out of raw HTML into the page title. The tsParticles background and the three research cards are kept **commented out** in the file (the particle library, its test and licence are still in the repo) so they can be revived. |
| `about.qmd` | Portrait, affiliation, CV link, bio. The "One loop does most of my work" block (intro sentence, stages, return line, application cards) is kept inside an HTML comment, so nothing from it shows; its CSS stays in the page `<style>`. Text column is 989px wide and centred via a page-level `main.content` rule, matching Research. No TOC. |
| `research.qmd` | Five project write-ups, each with figure or video, funding note and IEEE/arXiv links. Right-hand TOC with short labels from `{toc-text="..."}`, rewritten client-side by a script at the bottom. Loop videos autoplay on screen only. Ends with a "Publications →" link. |
| `publications.qmd` | Flat list, newest first, no year headings or TOC. See generation note below. |
| `mentoring.qmd` | Mentee list. |
| `for-fun.qmd` | "Leisure" (set by `pagetitle`, since the visible title is empty): flight-sim and photography galleries (flickr-justified-gallery + PhotoSwipe). Flight Simulation has `data-captions="off"`. |

`connect.qmd` and `custom-light.scss` exist but are not rendered or loaded. They are kept
on purpose in case they come back.

## Publications are generated — do not hand-edit

`publications-parsed.qmd` is produced from `publications.bib` by
`scripts/bib-to-quarto-parser.py`. Edit the `.bib` and re-run the script; edits made
directly to the parsed `.qmd` are overwritten on the next run. Venue lines use
`.publication-venue`; the "Co-first Authors" note has a grey leading `*`.

## Assets

Source assets in `assets/images/`, `assets/videos/`, `assets/unsplash-photos/`,
`assets/homepage/`, `assets/flight-sim/` and `assets/gallery-derivatives/` are versioned
so a fresh clone can fully `quarto render`. The rendered `docs/assets/` copies remain
versioned because GitHub Pages serves `docs/`.

`resources: assets/` publishes everything under `assets/`, so keep unreferenced
originals out of it: they live in `sources/unused-assets/`, which is not published.
`scripts/compress-photo.py` is a helper, not site code.

Figures are WebP, card fallbacks are 900 px JPEG, and all videos are muted, audio-free
H.264 with WebP posters.

Gallery captions: edit `scripts/gallery-content.json`, then run
`python3 scripts/generate-gallery-derivatives.py --captions-only` (no Pillow needed;
the caption test fails until you do). A full rebuild needs Pillow
(`scripts/requirements.txt`). `assets/gallery/gallery.js` honours `data-captions="off"`
on a gallery container and nudges Quarto's TOC scroll-spy after layout.

## Conventions

- Dark theme throughout; accent colour OSU `#FDD26E` (`--accent` in `styles.css`,
  `$link-color` and `$navbar-active-color` in `custom-dark.scss`). Navbar hover is `#e8e3d3`.
- One font family: Newsreader for everything (body, headings, navbar), loaded by one
  preconnected Google Fonts `<link>` in `_quarto.yml`. Source Sans 3 is used only for the
  TOC (`--font-toc`).
- Page width is global: `grid` in `_quarto.yml` (sidebar 200px, margin 200px, body 1200px).
  Do not add per-page grid blocks. The one exception is About, whose `main.content`
  gets the Research text width (989px) because it has no TOC column.
- Body copy justification uses the shared `.justify` class, or on Research a `main` rule.
  Do not target `main p` — Quarto wraps figure images in `<p>` and it drags images left.
  Do not wrap Research headings in a div: it stops Quarto building the TOC.
- `.funding` and `.publication-venue` are deliberately skewed (`skewX(-8deg)`), not italic.
- External links carry `target="_blank"` and `rel="noopener"`. The navbar Email icon opens
  a Gmail compose URL (no `mailto:`, which does nothing without a mail app).
- `assets/js/no-save.js` (loaded in the header) cancels right-click and drag on images and
  video as a casual-save deterrent. Photography is exempt entirely; Flight Simulation keeps
  the browser menu but blocks drag. It is a deterrent, not protection.
- Navbar icons are inline SVG (Font Awesome Free 6.7.2, CC BY 4.0; licence in
  `assets/vendor/fontawesome-icons/`). There is no Font Awesome CDN or Quarto extension.
- Scrollbar is hidden site-wide (`html { scrollbar-width: none }` in `styles.css`).
- Tests: `node --test scripts/*.cjs` and `python3 scripts/verify-site.py` (also run in CI via
  `.github/workflows/checks.yml`).

## Open items

- `maintenance.html` at the repo root is a self-contained "under maintenance" page with a
  canvas dot background (Georgia, no dependencies). The orphan `maintenance` branch holds only
  `docs/index.html` and `docs/404.html` copies of it, so pointing Pages at that branch and
  `/docs` takes the whole site to that page. Keep the branch copies identical to
  `maintenance.html` (re-copy after editing it). Restore by pointing Pages back to `main` and `/docs`.
- The search icon can briefly vanish on page switches in Brave (Quarto builds it client-side).
  Unfixed.

## Git

- Branches: `main` is what Pages serves. `maintenance` is an orphan branch, used only by
  pointing Pages at it during downtime. Work happens on short-lived feature branches and
  lands on `main` through a pull request. There is no permanent sandbox branch; make one
  from `main` when needed.
- Never force-push. Never push to `main` without explicit instruction.
- Old blobs from the removed `docs.bak/` trees still sit in history, so `.git` is ~115 MB
  despite the working tree being smaller. Shrinking it needs `git filter-repo` and a
  force-push — destructive, rewrites every SHA. Do not do this unprompted.
