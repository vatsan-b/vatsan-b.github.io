// Casual-save deterrent: blocks the context menu and dragging on images and
// video. The Photography gallery is left alone entirely. The Flight Simulation
// gallery keeps the browser menu (reload, inspect, ...) but still blocks drag.
(function () {
  var lastGallery = "";
  document.addEventListener("click", function (e) {
    var g = e.target.closest && e.target.closest("[data-gallery]");
    if (g) lastGallery = g.dataset.gallery;
  }, true);

  function isMedia(el) {
    return el && el.closest && el.closest("img, video, picture, .gallery-item, .pswp__img");
  }
  function exempt(el) {
    if (el.closest("[data-gallery='photography']")) return true;
    return !!el.closest(".pswp") && lastGallery === "photography";
  }

  function menuOk(el) {
    if (exempt(el)) return true;
    if (el.closest("[data-gallery='flight-sim']")) return true;
    return !!el.closest(".pswp") && lastGallery === "flight-sim";
  }

  document.addEventListener("contextmenu", function (e) {
    if (isMedia(e.target) && !menuOk(e.target)) e.preventDefault();
  });
  document.addEventListener("dragstart", function (e) {
    if (isMedia(e.target) && !exempt(e.target)) e.preventDefault();
  });
})();
