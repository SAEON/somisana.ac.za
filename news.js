(() => {
  const track = document.querySelector('#news-stories');
  const controls = document.querySelector('#news .news-controls');
  const [newer, older] = controls.querySelectorAll('button');

  function updateControls() {
    const end = track.scrollWidth - track.clientWidth;
    controls.hidden = end <= 1;
    newer.setAttribute('aria-disabled', track.scrollLeft <= 1);
    older.setAttribute('aria-disabled', track.scrollLeft >= end - 1);
  }

  function move(button, direction) {
    if (button.getAttribute('aria-disabled') === 'true') return;

    const [first, second] = track.children;
    const firstCard = first.getBoundingClientRect();
    const step = second.getBoundingClientRect().left - firstCard.left;
    const visible = Math.round((track.clientWidth + step - firstCard.width) / step);

    track.scrollBy({
      left: direction * visible * step,
      behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth',
    });
  }

  newer.addEventListener('click', () => move(newer, -1));
  older.addEventListener('click', () => move(older, 1));
  track.addEventListener('scroll', updateControls, { passive: true });
  new ResizeObserver(updateControls).observe(track);
  updateControls();
})();
