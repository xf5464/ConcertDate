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
          <div><h3 id="concertDialogTitle"></h3><p id="concertDialogSubtitle"></p></div>
          <button class="concert-dialog-close" type="button" aria-label="关闭" data-close-dialog>×</button>
        </div>
        <div id="concertDialogList" class="concert-dialog-list"></div>
      </section>`;
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

  const currentEventsForDate = dateString => data.concerts.filter(item => {
    if (item.date !== dateString) return false;
    if (state.city !== 'all' && item.city !== state.city) return false;
    if (state.theater !== 'all' && item.theater !== state.theater) return false;
    if (state.year !== 'all' && parseDateOnly(item.date).year !== Number(state.year)) return false;
    if (state.weekdays.length && !state.weekdays.includes(parseDateOnly(item.date).weekday)) return false;
    return true;
  });

  const openDialog = dateString => {
    const events = currentEventsForDate(dateString);
    if (!events.length) return;
    ensureDialog();
    const [year, month, day] = dateString.split('-').map(Number);
    document.getElementById('concertDialogTitle').textContent = `${year}年${month}月${day}日`;
    document.getElementById('concertDialogSubtitle').textContent = `${events.length} 场音乐会`;
    document.getElementById('concertDialogList').innerHTML = events.map(event => `
      <article class="concert-dialog-item">
        <h4>${escapeHtml(event.title)}</h4>
        <p>${escapeHtml(event.city)} · ${escapeHtml(event.theater)}</p>
        ${event.source ? `<a href="${escapeHtml(event.source)}" target="_blank" rel="noopener noreferrer">查看来源</a>` : ''}
      </article>`).join('');
    const dialog = document.getElementById('concertDialog');
    dialog.hidden = false;
    document.body.classList.add('dialog-open');
    dialog.querySelector('.concert-dialog-close')?.focus();
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
})();
