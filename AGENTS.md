# vatsan-b.github.io: personal website

Personal academic site for Srivatsan, live at <https://vatsan-b.github.io>. Static site
built with Quarto 1.10.18.

## Environment

- The repo lives in WSL at `/home/srivatsan/vatsan-b.github.io` (distro `Ubuntu2404`, which
  runs Ubuntu 26.04). Remote: `https://github.com/vatsan-b/vatsan-b.github.io.git`.
- Quarto is `/usr/local/bin/quarto`, Python is 3.14, `gh` is installed. Node is not needed
  for the site any more.
- WSL's Python has no Pillow. Only the gallery generator needs it (see Galleries).

## Build and deploy

- Pages are `.qmd` files at the repo root. `quarto render` builds them into `docs/`.
  GitHub Pages serves `docs/` from `main` (classic "deploy from a branch", no deploy
  workflow), so a push is the deploy. Pages caches files for 10 minutes.
- `docs/` is committed and duplicates `assets/` and `cv/`. That is normal Quarto output,
  not cruft: deleting it takes the site down. Never edit `docs/` by hand.
- A theme or SCSS edit renames the Bootstrap CSS in `docs/site_libs/` by hash; commit both
  the deleted and the new file.
- `.quarto/`, `temp/`, `*.bak/`, `__pycache__/`, `*:Zone.Identifier` are gitignored. Keep
  probe files in `temp/` and delete them when done.

## Pages

`_quarto.yml` renders exactly these six, in navbar order:

| Source | Page |
|---|---|
| `index.qmd` | Home. Headline and intro on the left, a muted loop video (`assets/videos/formlabs-sla-hsa.mp4`) on the right with a soft glow behind it (`.home-stage::before`, a 2%-step Gaussian gradient) and faint noise (`::after`) against banding. The page canvas is transparent; the navbar stays opaque. The headline is a `div role="heading"`, because Quarto lifts a raw `<h1>` into the title block. |
| `about.qmd` | Portrait, affiliation, CV link, bio. `main.content` is 989px wide and centred (the Research text width, since About has no TOC). |
| `research.qmd` | Six projects with figure or video, funding note and links. Right-hand TOC with short labels from `{toc-text="..."}`, applied by the script at the bottom. Ends with a "Publications →" link. |
| `publications.qmd` | Includes the generated `publications-parsed.qmd` (see Scripts). Flat list, newest first. |
| `mentoring.qmd` | "Mentorship": intro and mentee list (names use `.mentee-name`, weight 500). |
| `for-fun.qmd` | "Leisure" (`pagetitle`; the visible title is empty): flight-sim and photography galleries, right-hand TOC. |

## Styles

- Themes: `theme: {dark: [darkly, custom-dark.scss], light: [default, custom-light.scss]}`.
  Dark is listed first, so it is the default; `respect-user-color-scheme: true` follows the
  visitor's system setting on a first visit, and the navbar toggle (saved in localStorage)
  overrides it. Quarto puts `quarto-dark` or `quarto-light` on `<body>`.
- `styles.css` holds every shared rule. Colours are variables at its top: `:root` is dark,
  `:root:has(body.quarto-light)` overrides for light. Main ones: `--page-bg` (r, g, b of page
  and navbar: dark `31, 31, 35`, light `240, 238, 230`), `--accent` (`#FDD26E` / `#D73F09`),
  `--text-dark`, `--text-caption`, `--glow` and `--glow-peak` (home glow colour and strength),
  `--frame-shadow`, the search panel colours and `--gallery-bg`. Add colours as variables
  there, never as hex in a page, or they will not switch with the theme.
- The accent also lives in the SCSS (`$link-color`, `$navbar-active-color`), so a recolour
  touches `styles.css` and both SCSS files. `custom-dark.scss` sets `$web-font-path: false`
  so darkly does not import Lato from Google. `custom-light.scss` sets
  `$navbar-padding-y: 1rem` so the navbar height matches dark.
- Motion variables in `styles.css`: `--motion-fast` 0.3s (page fade), `--motion-base` 0.4s,
  `--motion-slow` 0.6s, `--ease`, `--ease-out`. Every transition and animation uses them,
  including `assets/gallery/gallery.css`. `prefers-reduced-motion` turns off the page fade and
  smooth scrolling.
- Shared classes: `.cover-video` (video filling its frame), `.media-figure` and
  `.video-figure` (centred figure blocks), `.video-frame` and `.ratio-*` (Research, defined in
  its `<style>`), `.justify`, `.funding` and `.publication-venue` (skewed, not italic).
- Width is global: `grid` in `_quarto.yml` (sidebar 200, body 1200, margin 200) plus
  `#quarto-content { max-width: 1300px }`. Do not add per-page grids.
- The scrollbar is hidden site-wide (`html { scrollbar-width: none }`).

## Fonts

Self-hosted in `assets/fonts/` (exact Google Fonts latin files, SIL OFL licences beside
them), declared with `@font-face` at the top of `styles.css`. Newsreader (variable, roman and
italic) is used everywhere; Source Sans 3 only in the TOC (`--font-toc`). The roman
Newsreader file is preloaded from `_quarto.yml`. No request goes to Google Fonts.

## Galleries

- `scripts/gallery-content.json` is the hand-edited input: source file (under
  `sources/gallery-originals/`) and caption per image, in display order, per gallery
  (`flight-sim`, `photography`).
- `scripts/generate-gallery-derivatives.py` writes, per image, into
  `assets/gallery-derivatives/<gallery>/<slug>/`: `thumb-<w>.avif` and `.webp` (400/800/1200,
  never wider than the source), `medium-<w>.webp` (1200/1920, only below the full size) and
  `full-<w>.webp` (long edge at most 2560). All carry no metadata. It also writes
  `manifest.json`, one image per line: `{caption, slug, width, height, thumbs, mediums}`.
  The manifest names no source file, so original file names and `sources/` stay unpublished.
  Flags: none = build what is missing (needs Pillow with AVIF), `--force` = re-encode all,
  `--captions-only` = copy captions into the manifest, matched by order and slug (no Pillow).
  Files the manifest no longer lists are deleted.
- The Windows Python has Pillow without AVIF: it can rerun the generator when no new AVIF
  is needed. A new image needs a Pillow with AVIF; ask before installing one.
- `for-fun.qmd` loads the gallery CSS through its `css:` front matter and, through
  `include-in-header`, preloads the manifest and loads fjGallery, the PhotoSwipe lightbox and
  `assets/gallery/gallery.js` (an ES module). `gallery.js` fetches the manifest once, builds
  the tile URLs from the file-name pattern, lays tiles out with fjGallery and wires PhotoSwipe.
  The PhotoSwipe core is imported only on the first click. Tile links carry `data-no-instant`
  so instant.page does not prefetch full images on hover. Options are `data-*` attributes on
  the container: `data-row-height`, `-md`, `-sm`, and `data-captions="off"` (flight-sim).

## Site-wide includes

`_quarto.yml` adds to every page: the font preload, instant.page
(`assets/vendor/instant-page/5.2.0/`, prefetches a page when its link is hovered),
`assets/js/no-save.js` and `assets/js/autoplay-video.js`. Google Analytics is set with
`google-analytics` and stays. `favicon.png` is in `assets/images/`.

- `autoplay-video.js` plays `video[data-autoplay]` while a quarter of it is on screen and
  pauses it otherwise; under `prefers-reduced-motion` the poster stays.
- `no-save.js` blocks the right-click menu and dragging on images and video. Photography
  allows both; Flight Simulation allows the menu but blocks drag. It only deters casual saving.
- Third-party code is vendored under `assets/vendor/<name>/<version>/` with its licence.
  Navbar icons are inline SVG from Font Awesome Free 6.7.2 (licence in
  `assets/vendor/fontawesome-icons/`).

## Scripts and checks

- `python3 scripts/check-site.py` is the only check (standard library, 12 checks: local
  links and fragments, srcset spaces, alt text, `rel="noopener"`, comments and stray fences,
  duplicate ids, media sizes, gallery manifest and captions, publications up to date, `docs/`
  copy of `assets/` and `cv/`, image metadata, unpublished paths). Run it after
  `quarto render`; it exits 1 on any failure. `check-site.py OTHER_COPY` checks another copy.
- `python3 scripts/bib-to-quarto-parser.py` rebuilds `publications-parsed.qmd` from
  `publications.bib`. Never hand-edit the parsed file.
- CI (`.github/workflows/checks.yml`) runs only `check-site.py` (Python 3.14, read-only
  permissions) on pushes to `main` and pull requests. It does not render or deploy.

## Kept but not published

`resources:` publishes everything under `assets/` and `cv/`, so nothing private or unused
may sit there.

- `sources/gallery-originals/`: gallery originals. Some carry GPS or camera serials; never
  move them back under `assets/`.
- `sources/disabled-features/`: switched-off features (home particles with tsParticles, home
  research cards and their images, the About "work loop" block, the `connect.qmd` page). Its
  `README.md` says how to restore each.
- `sources/unused-assets/`: images not used on any page.

## Conventions

- Content lives in the `.qmd` files. Shared CSS goes in `styles.css`; CSS and JS for one
  page go in a `<style>` or `<script>` block in that page.
- No new inline styles. The ones left are deliberate and tuned by hand: the top-margin
  wrappers on About and Mentorship, the CV link, the per-video `aspect-ratio` and
  `object-position` on Research, and the grey link lines the parser writes.
- To switch a feature off, move it to `sources/disabled-features/` with restore notes;
  do not leave commented-out code in pages. Moves are reversible (`git mv`).
- Research text is justified by a `main` rule. Do not target `main p` (Quarto wraps figure
  images in `<p>`) and do not wrap the headings in a div (it breaks the TOC).
- External links carry `target="_blank"` and `rel="noopener"`. The navbar Email icon opens a
  Gmail compose URL, since `mailto:` does nothing without a mail app.

## Known open items

- The grey publication link lines fail contrast; changing them is the owner's visual call.
- `.git` is about 116 MB because old blobs (removed `docs.bak/`, originals) stay in history.
  Only a history rewrite and force-push would shrink it; that is the owner's decision.
- Breakpoints 860px (home hero) and 992px (navbar and gallery) are left as they are.
- `$body-bg` in `custom-light.scss` is the older `#faf9f5`; `--page-bg` covers the page,
  but anything using Bootstrap's own background variable shows it.
- The search icon can briefly vanish on page switches in Brave (Quarto builds it in JS).
- `maintenance.html` is a standalone "under maintenance" page. The orphan `maintenance`
  branch holds copies of it as `docs/index.html` and `docs/404.html`; pointing Pages at that
  branch shows it site-wide. Keep the copies identical when editing it.

## Git

- `main` is what Pages serves; `maintenance` is the orphan branch above. Small changes go
  straight to `main`; branches and pull requests only when Sri asks.
- Never commit, push or force-push without his explicit go. Use `git mv` / `git rm` for
  tracked files.
