(() => {
  const CALENDAR_MIN_SCROLL_TOP = 0;
  const EPSILON = 2;

  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'quick-top-button';
  button.setAttribute('aria-label', '返回上方');
  button.setAttribute('title', '返回上方');
  button.textContent = '↑';
  document.body.appendChild(button);

  button.addEventListener('click', () => {
    const scroller = document.getElementById('calendarScroller');

    if (scroller && scroller.scrollTop > CALENDAR_MIN_SCROLL_TOP + EPSILON) {
      scroller.scrollTo({
        top: CALENDAR_MIN_SCROLL_TOP,
        behavior: 'smooth'
      });
      return;
    }

    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  });
})();
