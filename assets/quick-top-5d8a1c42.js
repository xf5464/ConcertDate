(() => {
  const CALENDAR_VIEWPORT_TOP = 0; // A
  const EPSILON = 3;

  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'quick-top-button';
  button.setAttribute('aria-label', '切换日历到顶部 / 页面顶部');
  button.setAttribute('title', '切换日历到顶部 / 页面顶部');
  button.textContent = '↑';
  document.body.appendChild(button);

  const runway = document.createElement('div');
  runway.className = 'quick-top-scroll-runway';
  runway.setAttribute('aria-hidden', 'true');
  document.body.appendChild(runway);

  function updateRunway() {
    const panel = document.querySelector('.calendar-panel');
    if (!panel) return;

    runway.style.height = '0px';
    const panelDocumentTop = window.scrollY + panel.getBoundingClientRect().top;
    const currentMaxScroll = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
    const extra = Math.max(0, panelDocumentTop - CALENDAR_VIEWPORT_TOP - currentMaxScroll);
    runway.style.height = `${Math.ceil(extra + 12)}px`;
  }

  function moveCalendarPanelToA() {
    const panel = document.querySelector('.calendar-panel');
    if (!panel) return false;

    updateRunway();
    const currentTop = panel.getBoundingClientRect().top;
    if (Math.abs(currentTop - CALENDAR_VIEWPORT_TOP) <= EPSILON) return false;

    const target = Math.max(0, window.scrollY + currentTop - CALENDAR_VIEWPORT_TOP);
    window.scrollTo({ top: target, behavior: 'smooth' });
    return true;
  }

  button.addEventListener('click', () => {
    // First click: move the whole page until the calendar panel reaches A (default 0).
    // If it is already at A, the next click returns the whole page to its initial top.
    if (moveCalendarPanelToA()) return;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  window.addEventListener('resize', updateRunway);
  window.addEventListener('load', updateRunway);
  setTimeout(updateRunway, 100);
})();
