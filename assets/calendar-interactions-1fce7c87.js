(() => {
  const scroller = document.getElementById('calendarScroller');
  if (!scroller) return;

  const ensureDialog = () => {
    if (document.getElementById('concertDialog')) return;
    const dialog = document.createElement('div');
    dialog.id = 'concertDialog';
    dialog.className = 'concert-dialog';
    dialog.hidden = true;
    dialog.innerHTML = `
      <div class="concert-dialog-backdrop" data-close-dialog></div>
      <section class="concert-dialog-card" role="dialog" aria-modal="true" aria-labelledby="concertDialogTitle">
        <div class="concert-dialog-header">
          <div>
            <h3 id="concertDialogTitle"></h3>
            <p id="concertDialogSubtitle"></p>
          </div>
          <button class="concert-dialog-close" type="button" aria-label="关闭" data-close-dialog>×</button>
        </div>
        <div id="concertDialogList" class="concert-dialog-list"></div>
      </section>
    `;
    document.body.appendChild(dialog);

    dialog.addEventListener('click', event => {
      if (event.target.closest('[data-close-dialog]')) closeDialog();
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && !dialog.hidden) closeDialog();
    });
  };

  const closeDialog = () => {
    const dialog = document.getElementById('concertDialog');
    if (!dialog) return;
    dialog.hidden = true;
    document.body.classList.remove('dialog-open');
  };

  const currentEventsForDate = dateString => {
    return data.concerts.filter(item => {
      if (item.date !== dateString) return false;
      if (state.city !== 'all' && item.city !== state.city) return false;
      if (state.theater !== 'all' && item.theater !== state.theater) return false;
      if (state.weekday !== 'all') {
        const d = parseDateOnly(item.date);
        if (d.weekday !== Number(state.weekday)) return false;
      }
      return true;
    });
  };

  const openDialog = dateString => {
    const events = currentEventsForDate(dateString);
    if (!events.length) return;

    ensureDialog();
    const dialog = document.getElementById('concertDialog');
    const title = document.getElementById('concertDialogTitle');
    const subtitle = document.getElementById('concertDialogSubtitle');
    const list = document.getElementById('concertDialogList');

    const [year, month, day] = dateString.split('-').map(Number);
    title.textContent = `${year}年${month}月${day}日`;
    subtitle.textContent = `${events.length} 场音乐会`;
    list.innerHTML = events.map(event => `
      <article class="concert-dialog-item">
        <h4>${escapeHtml(event.title)}</h4>
        <p>${escapeHtml(event.city)} · ${escapeHtml(event.theater)}</p>
        ${event.source ? `<a href="${escapeHtml(event.source)}" target="_blank" rel="noopener noreferrer">查看来源</a>` : ''}
      </article>
    `).join('');

    dialog.hidden = false;
    document.body.classList.add('dialog-open');
    dialog.querySelector('.concert-dialog-close')?.focus();
  };

  const enhanceCalendar = () => {
    document.querySelectorAll('.month-card').forEach(monthCard => {
      const month = Number(monthCard.dataset.month);
      monthCard.querySelectorAll('.day:not(.empty)').forEach(dayEl => {
        const dayNumber = Number(dayEl.querySelector('.day-number')?.textContent);
        if (!dayNumber) return;

        const dateString = formatDate(state.year, month + 1, dayNumber);
        dayEl.dataset.date = dateString;

        if (dayEl.classList.contains('has-concert')) {
          dayEl.classList.add('concert-clickable');
          const eventList = dayEl.querySelector('.event-list');
          if (eventList && !eventList.querySelector('.concert-marker')) {
            eventList.innerHTML = '<span class="concert-marker" aria-hidden="true"></span>';
          }
        } else {
          dayEl.classList.remove('concert-clickable');
        }
      });
    });
  };

  scroller.addEventListener('click', event => {
    const dayEl = event.target.closest('.day.concert-clickable');
    if (!dayEl || !scroller.contains(dayEl)) return;
    openDialog(dayEl.dataset.date);
  });

  scroller.addEventListener('keydown', event => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    const dayEl = event.target.closest('.day.concert-clickable');
    if (!dayEl || !scroller.contains(dayEl)) return;
    event.preventDefault();
    openDialog(dayEl.dataset.date);
  });

  const observer = new MutationObserver(() => enhanceCalendar());
  observer.observe(scroller, { childList: true, subtree: true });
  enhanceCalendar();
})();
