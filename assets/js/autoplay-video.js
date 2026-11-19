// Loop videos marked with data-autoplay (home page and Research) play only
// while at least a quarter of them is on screen, and pause otherwise.
// Visitors who ask for reduced motion see the poster frame instead; if they
// switch that setting off again, the visible videos start playing.
(() => {
  const videos = document.querySelectorAll('video[data-autoplay]');
  if (!videos.length || !('IntersectionObserver' in window)) return;

  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const onScreen = new Set();

  const update = (video) => {
    if (onScreen.has(video) && !reducedMotion.matches) {
      video.play().catch(() => {}); // the browser may refuse; the poster stays
    } else {
      video.pause();
    }
  };

  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting) onScreen.add(entry.target);
      else onScreen.delete(entry.target);
      update(entry.target);
    }
  }, { threshold: 0.25 });

  videos.forEach((video) => observer.observe(video));
  reducedMotion.addEventListener('change', () => videos.forEach(update));
})();
