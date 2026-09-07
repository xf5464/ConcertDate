(() => {
  const CALENDAR_VIEWPORT_TOP = 0;
  const EPSILON = 4;
  let focused = false;
  let restoreScrollY = 0;

  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'quick-top-button';
  button.setAttribute('aria-label', '展开日历');
  button.setAttribute('title', '展开日历');
  button.textContent = '↑';
  document.body.appendChild(button);

  const runway = document.createElement('div');
  runway.className = 'quick-top-scroll-runway';
  runway.setAttribute('aria-hidden', 'true');
  document.body.appendChild(runway);

  function updateButton() {
    button.textContent = focused ? '↓' : '↑';
    button.setAttribute('aria-label', focused ? '还原页面位置' : '展开日历');
    button.setAttribute('title', focused ? '还原页面位置' : '展开日历');
  }

  function updateRunway() {
    const panel = document.querySelector('.calendar-panel');
    if (!panel) return;

    runway.style.height = '0px';
    if (focused) {
      // Keep enough document height so the calendar panel can sit flush at A=0.
      const panelDocumentTop = window.scrollY + panel.getBoundingClientRect().top;
      const maxScroll = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
      const needed = Math.max(0, panelDocumentTop - CALENDAR_VIEWPORT_TOP - maxScroll);
      runway.style.height = `${Math.ceil(needed + window.innerHeight * 0.15)}px`;
    }
  }

  function focusCalendar() {
    const panel = document.querySelector('.calendar-panel');
    if (!panel) return;

    restoreScrollY = window.scrollY;
    focused = true;
    document.body.classList.add('quick-calendar-focus');
    updateRunway();
    updateButton();

    requestAnimationFrame(() => {
      updateRunway();
      const top = window.scrollY + panel.getBoundingClientRect().top - CALENDAR_VIEWPORT_TOP;
      window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
    });
  }

  function restorePage() {
    focused = false;
    document.body.classList.remove('quick-calendar-focus');
    runway.style.height = '0px';
    updateButton();
    window.scrollTo({ top: restoreScrollY, behavior: 'smooth' });
  }

  button.addEventListener('click', () => {
    if (focused) restorePage();
    else focusCalendar();
  });

  window.addEventListener('resize', () => {
    if (!focused) return;
    updateRunway();
    const panel = document.querySelector('.calendar-panel');
    if (!panel) return;
    const currentTop = panel.getBoundingClientRect().top;
    if (Math.abs(currentTop - CALENDAR_VIEWPORT_TOP) > EPSILON) {
      window.scrollBy({ top: currentTop - CALENDAR_VIEWPORT_TOP, behavior: 'auto' });
    }
  });

  updateButton();
})();
