// Casual-save deterrent, loaded on every page: blocks the right-click menu
// and dragging on images and video. Only deters casual saving.
// Exemptions by gallery (the data-gallery value on for-fun.qmd):
//   photography  menu and drag both allowed
//   flight-sim   browser menu allowed (reload, inspect, ...), drag blocked
{
  const MENU_ALLOWED = ["photography", "flight-sim"];
  const DRAG_ALLOWED = ["photography"];

  // The lightbox (.pswp) is added at the end of <body>, outside the gallery,
  // so remember which gallery was clicked last to know whose photo it shows.
  let lastGallery = "";
  document.addEventListener("click", (e) => {
    const g = e.target instanceof Element && e.target.closest("[data-gallery]");
    if (g) lastGallery = g.dataset.gallery;
  }, true);

  // null if el is not an image, video or tile; otherwise the name of its
  // gallery ("" for media outside any gallery). Lightbox images count as
  // part of the last clicked gallery. .pswp__img also covers the lightbox's
  // placeholder, which is a <div> while the full image loads.
  const mediaGallery = (el) => {
    if (!(el instanceof Element) || !el.closest("img, video, picture, .gallery-item, .pswp__img")) return null;
    const g = el.closest("[data-gallery]");
    if (g) return g.dataset.gallery;
    return el.closest(".pswp") ? lastGallery : "";
  };

  // Cancel the event on media unless its gallery is in the allowed list.
  const guard = (allowed) => (e) => {
    const gallery = mediaGallery(e.target);
    if (gallery !== null && !allowed.includes(gallery)) e.preventDefault();
  };

  document.addEventListener("contextmenu", guard(MENU_ALLOWED));
  document.addEventListener("dragstart", guard(DRAG_ALLOWED));
}
