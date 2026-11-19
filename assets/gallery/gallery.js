/* Leisure page galleries (for-fun.qmd).
 *
 * Every element with data-gallery="<name>" becomes a justified grid of the
 * images listed under that name in the manifest, which
 * scripts/generate-gallery-derivatives.py writes. Clicking a tile opens the
 * PhotoSwipe lightbox. Options per gallery, as attributes on the element:
 *   data-row-height, -md, -sm   row height in px on wide, medium (< 992 px)
 *                               and small (< 760 px) screens
 *   data-captions="off"         no caption in the lightbox
 *
 * Loaded as a module after the deferred fjGallery and PhotoSwipe lightbox
 * scripts, whose globals (fjGallery, PhotoSwipeLightbox) it uses.
 */

const MANIFEST_URL = "assets/gallery-derivatives/manifest.json";
const IMAGE_ROOT = "assets/gallery-derivatives";
const RESIZE_DELAY_MS = 200;

// Magnifier icon shown on hover (Font Awesome "magnifying-glass-plus").
const ZOOM_ICON =
  '<span class="gallery-hover-icon"><svg class="nav-icon" aria-hidden="true" fill="currentColor" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><path d="M416 208c0 45.9-14.9 88.3-40 122.7L502.6 457.4c12.5 12.5 12.5 32.8 0 45.3s-32.8 12.5-45.3 0L330.7 376c-34.4 25.2-76.8 40-122.7 40C93.1 416 0 322.9 0 208S93.1 0 208 0S416 93.1 416 208zM184 296c0 13.3 10.7 24 24 24s24-10.7 24-24l0-64 64 0c13.3 0 24-10.7 24-24s-10.7-24-24-24l-64 0 0-64c0-13.3-10.7-24-24-24s-24 10.7-24 24l0 64-64 0c-13.3 0-24 10.7-24 24s10.7 24 24 24l64 0 0 64z"/></svg></span>';

const fetchJson = async (url) => {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`gallery data fetch failed: ${res.status}`);
  return res.json();
};

// Turns {name: value} into ' name="value"', escaping every value the same way.
// A value of true writes a bare attribute; false, null or undefined skips it.
const ENTITIES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
const attrs = (pairs) =>
  Object.entries(pairs)
    .filter(([, value]) => value != null && value !== false)
    .map(([name, value]) =>
      value === true ? ` ${name}` : ` ${name}="${String(value).replace(/[&<>"']/g, (c) => ENTITIES[c])}"`)
    .join("");

// Row heights from the data-row-height attributes; each size falls back to
// the next larger one.
const readRowHeights = (el) => {
  const wide = parseInt(el.dataset.rowHeight, 10) || 200;
  const md = parseInt(el.dataset.rowHeightMd, 10) || wide;
  const sm = parseInt(el.dataset.rowHeightSm, 10) || md;
  return { wide, md, sm };
};

const currentRowHeight = ({ wide, md, sm }) =>
  window.innerWidth < 760 ? sm : window.innerWidth < 992 ? md : wide;

// A justified tile is about rowHeight * aspect ratio wide, so tell the
// browser that width (wide panoramas need a bigger thumbnail).
const sizesFor = (item, rowHeight) => `${Math.ceil((rowHeight * item.width) / item.height)}px`;

// Manifest entry -> tile markup. File names follow the generator's pattern:
// thumb-<w>.avif/.webp, medium-<w>.webp and full-<width>.webp in one folder.
const tileMarkup = (gallery, item, rowHeight, showCaptions) => {
  const dir = `${IMAGE_ROOT}/${gallery}/${item.slug}`;
  const full = `${dir}/full-${item.width}.webp`;
  const thumbSrcset = (ext) => item.thumbs.map((w) => `${dir}/thumb-${w}.${ext} ${w}w`).join(", ");
  const lightboxSrcset = [
    ...item.mediums.map((w) => `${dir}/medium-${w}.webp ${w}w`),
    `${full} ${item.width}w`,
  ].join(", ");
  const middleThumb = item.thumbs[Math.floor(item.thumbs.length / 2)];

  const link = attrs({
    class: "gallery-item",
    "data-no-instant": true, // stops instant.page prefetching the lightbox image on hover
    href: full,
    "data-caption": showCaptions && item.caption ? item.caption : null,
    "data-pswp-srcset": lightboxSrcset,
    "data-pswp-width": item.width,
    "data-pswp-height": item.height,
  });
  // Both need the sizes hint: the browser reads it from whichever one it picks.
  const sizes = sizesFor(item, rowHeight);
  const avif = attrs({ type: "image/avif", srcset: thumbSrcset("avif"), sizes });
  const img = attrs({
    src: `${dir}/thumb-${middleThumb}.webp`,
    srcset: thumbSrcset("webp"),
    sizes,
    width: item.width, // fjGallery reads these for the aspect ratio before the image loads
    height: item.height,
    alt: item.caption || "Photograph",
    loading: "lazy",
    decoding: "async",
  });
  return `<a${link}><picture><source${avif}><img${img}></picture>${ZOOM_ICON}</a>`;
};

// Adds the caption bar to the lightbox; the text comes from the clicked
// tile's data-caption, so galleries with captions off show nothing.
const addCaption = (lightbox) => {
  lightbox.on("uiRegister", () => {
    lightbox.pswp.ui.registerElement({
      name: "custom-caption",
      order: 9,
      isButton: false,
      appendTo: "root",
      tagName: "div",
      className: "pswp__custom-caption",
      onInit: (el) => {
        lightbox.pswp.on("change", () => {
          el.textContent = lightbox.pswp.currSlide?.data.element?.dataset.caption || "";
        });
      },
    });
  });
};

const initGallery = (container, items) => {
  const gallery = container.dataset.gallery;
  const rowHeights = readRowHeights(container);
  const rowHeight = currentRowHeight(rowHeights);
  const showCaptions = container.dataset.captions !== "off";
  container.innerHTML = items.map((item) => tileMarkup(gallery, item, rowHeight, showCaptions)).join("");

  fjGallery(container, {
    itemSelector: ".gallery-item",
    rowHeight,
    gutter: 10,
    lastRow: "left",
    rowHeightTolerance: 0.25,
    // fjGallery re-justifies as each thumbnail loads; with a transition every
    // pass would animate all tiles for 0.3 s.
    transitionDuration: false,
    onJustify: () => {
      container.classList.add("is-ready"); // fades the grid in (gallery.css)
      // The page just grew. Quarto's TOC scroll-spy only re-checks on scroll
      // or resize, so nudge it to pick the right heading.
      requestAnimationFrame(() => document.dispatchEvent(new Event("scroll")));
    },
  });

  const lightbox = new PhotoSwipeLightbox({
    gallery: container,
    children: ".gallery-item",
    // The lightbox core is only downloaded on the first click. It is a UMD
    // build: importing it runs it, and it sets window.PhotoSwipe.
    pswpModule: () =>
      import("../vendor/photoswipe/5.4.4/photoswipe.umd.min.js").then(() => window.PhotoSwipe),
    showHideAnimationType: "zoom",
    bgOpacity: 0.9,
  });
  addCaption(lightbox);
  lightbox.init();

  return { container, items, rowHeights, rowHeight };
};

// One debounced resize listener for every gallery: when the breakpoint
// changes the row height, update the thumbnail sizes and re-justify.
const watchResize = (galleries) => {
  let timer;
  window.addEventListener("resize", () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      for (const g of galleries) {
        const next = currentRowHeight(g.rowHeights);
        if (next === g.rowHeight) continue;
        g.rowHeight = next;
        g.container.querySelectorAll("picture").forEach((picture, i) => {
          const sizes = sizesFor(g.items[i], next);
          picture.querySelectorAll("source, img").forEach((el) => { el.sizes = sizes; });
        });
        fjGallery(g.container, "updateOptions", { rowHeight: next });
      }
    }, RESIZE_DELAY_MS);
  });
};

const containers = [...document.querySelectorAll("[data-gallery]")];
if (containers.length) {
  fetchJson(MANIFEST_URL)
    .then((manifest) => {
      const galleries = containers
        .map((el) => [el, manifest.galleries?.[el.dataset.gallery] ?? []])
        .filter(([, items]) => items.length)
        .map(([el, items]) => initGallery(el, items));
      watchResize(galleries);
    })
    .catch((err) => {
      console.error("gallery init failed:", err);
      // Reveal the (empty) containers rather than leave invisible gaps.
      containers.forEach((el) => el.classList.add("is-ready"));
    });
}
