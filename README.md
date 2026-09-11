# Srivatsan Balaji - Portfolio

Personal website / academic portfolio, publicly hosted via GitHub Pages. Source files are here for hosting and for anyone curious about how it's put together.


Developed with help from [Claude](https://claude.com/product/overview) and [Codex](https://chatgpt.com/codex/?c_id=23226184784&c_agid=193454751742&c_crid=807823907959&c_kwid=kwd-111182835&c_ims=&c_pms=9061900&c_nw=g&c_dvc=c)

---
Currently managed by [Hermes Agent](https://hermes-agent.nousresearch.com/)

## Tuning the homepage constellation

Edit only the `SETTINGS` block near the top of `index.qmd`. No library edits or npm install required.

| Setting | Default | Effect |
| --- | --- | --- |
| `speed` | `0.18` | Lower values drift more slowly. |
| `colors` | Gold, gold, pale blue | Hex particle colours; repeating gold weights the palette. |
| `particleCount` | `75` | Fixed desktop budget, independent of screen area. |
| `mobileParticleCount` | `35` | Budget at widths up to 760 CSS pixels. |
| `particleSize` | `0.8–1.8` | Dot radius range. |
| `particleOpacity` | `0.25–0.65` | Dot opacity range, between 0 and 1. |
| `linkColor` | `#FDD26E` | Connection colour. |
| `linkDistance` | `150` | Maximum connection distance in CSS pixels. |
| `linkOpacity` | `0.18` | Connection brightness, between 0 and 1. |
| `fps` | `30` | Drawing frame-rate cap. Try 20 for a lower budget. |

For an even lighter effect, try 50 desktop particles, 25 mobile particles, and 20 fps. Increasing particle counts and connection distance costs more than changing colours or drift speed. Retina scaling, hover/click physics, shadows, and pulsing are disabled. Hidden tabs pause; reduced-motion preferences render a static constellation, including preference changes while the page is open. A plain dark background remains if JavaScript fails.

After editing, run `quarto render index.qmd`, `node --test scripts/test-constellation.cjs`, and `python3 scripts/verify-site.py`. Preview with `python3 -m http.server 8765 --directory docs` and open http://localhost:8765. Commit both the source and rendered output when approved; GitHub Pages serves `docs/`, not the source. Rendering only the homepage avoids publishing unrelated source/output differences on other pages.

The animation uses [tsParticles Slim](https://github.com/tsparticles/tsparticles) 3.9.1 (MIT), vendored under `assets/vendor/tsparticles/3.9.1/` with its license. Original bundle: https://cdn.jsdelivr.net/npm/@tsparticles/slim@3.9.1/tsparticles.slim.bundle.min.js. Quarto copies it into `docs/assets/`; visitors do not depend on a CDN or your laptop. Keep the bundle pinned and test real canvas links, colours, mobile resizing, and reduced-motion behavior before upgrading major versions.
