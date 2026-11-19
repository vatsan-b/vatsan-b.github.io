# Disabled features

Features that are switched off but kept so they can come back. Nothing in this
folder is published: `_quarto.yml` only renders the pages in its `render:` list and
only copies `cv/` and `assets/` into the site.

| File | What it is | How to put it back |
|---|---|---|
| `homepage-particles.html` | Drifting gold dots and lines behind the home page (tsParticles 3.9.1, library and licence in `tsparticles/`). | Move `tsparticles/` back to `assets/vendor/tsparticles/`. Copy the three parts of the file (markup line, CSS, script) into `index.qmd` as the comments in the file say. |
| `homepage-cards.html` | Three image cards linking to Research, under the home hero. Images in `homepage-card-images/`. | Move `homepage-card-images/` back to `assets/homepage/`. Copy the CSS into the `<style>` block of `index.qmd` and the markup into a ```` ```{=html} ```` fence after the hero. |
| `about-work-loop.html` | The "One loop does most of my work" diagram (design, fabricate, characterize, compute) with its focus cards. | Copy the CSS into the `<style>` block of `about.qmd` and the markup into a ```` ```{=html} ```` fence at the end of the text block. |
| `connect.qmd` | A "Connect" page with five icon boxes (email, LinkedIn, Scholar, GitHub, Unsplash). Its CSS is at the bottom of the file. | Move it back to the repo root, add `connect.qmd` to `render:` (and the navbar if wanted) in `_quarto.yml`, and remove `connect.html` from `UNPUBLISHED` in `scripts/check-site.py`. |

Then run `quarto render` and check the page in both themes. Raw HTML must sit inside a
```` ```{=html} ```` fence, or Quarto shows it as text.
