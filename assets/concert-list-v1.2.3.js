(() => {
  const button = document.getElementById('concertListButton');
  if (!button) return;

  const WEEKDAY_NAMES = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];

  function currentFilteredConcerts() {
    if (typeof data === 'undefined' || !Array.isArray(data.concerts)) return [];
    return data.concerts
      .filter(item => typeof eventMatches === 'function' ? eventMatches(item) : true)
      .slice()
      .sort((a, b) => String(a.date).localeCompare(String(b.date)) || String(a.theater).localeCompare(String(b.theater)) || String(a.title).localeCompare(String(b.title)));
  }

  function formatDateMeta(dateString) {
    const [year, month, day] = String(dateString).split('-').map(Number);
    const weekday = WEEKDAY_NAMES[new Date(Date.UTC(year, month - 1, day)).getUTCDay()];
    return `${year}年${month}月${day}日 · ${weekday}`;
  }

  function closePanel() {
    const overlay = document.getElementById('concertListOverlay');
    if (!overlay) return;
    overlay.hidden = true;
    document.body.classList.remove('concert-list-open');
  }

  function ensurePanel() {
    let overlay = document.getElementById('concertListOverlay');
    if (overlay) return overlay;

    overlay = document.createElement('div');
    overlay.id = 'concertListOverlay';
    overlay.className = 'concert-list-overlay';
    overlay.hidden = true;
    overlay.innerHTML = `
      <div class="concert-list-backdrop" data-concert-list-close></div>
      <section class="concert-list-card" role="dialog" aria-modal="true" aria-labelledby="concertListTitle">
        <div class="concert-list-header">
          <div>
            <h3 id="concertListTitle">音乐会列表</h3>
            <p id="concertListSubtitle"></p>
          </div>
          <button type="button" class="concert-list-close" aria-label="关闭" data-concert-list-close>×</button>
        </div>
        <div id="concertListItems" class="concert-list-items"></div>
      </section>`;
    document.body.appendChild(overlay);

    overlay.addEventListener('click', event => {
      if (event.target.closest('[data-concert-list-close]')) closePanel();
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && !overlay.hidden) closePanel();
    });
    return overlay;
  }

  function openPanel() {
    const overlay = ensurePanel();
    const items = currentFilteredConcerts();
    const list = document.getElementById('concertListItems');
    const subtitle = document.getElementById('concertListSubtitle');

    subtitle.textContent = `当前筛选条件 · ${items.length} 场`;

    if (!items.length) {
      list.innerHTML = '<div class="concert-list-empty">当前筛选条件下没有音乐会。</div>';
    } else {
      list.innerHTML = items.map(item => {
        const color = typeof colorForTheater === 'function' ? colorForTheater(item.theater) : '#22c55e';
        return `
          <article class="concert-list-item">
            <div class="concert-list-meta">${formatDateMeta(item.date)}</div>
            <div class="concert-list-theater"><span class="concert-list-dot" style="--concert-list-dot:${color}"></span>${escapeHtml(item.theater || '')}</div>
            <h4>${escapeHtml(item.title || '未命名音乐会')}</h4>
            ${item.source ? `<a href="${escapeHtml(item.source)}" target="_blank" rel="noopener noreferrer">查看来源</a>` : ''}
          </article>`;
      }).join('');
    }

    overlay.hidden = false;
    document.body.classList.add('concert-list-open');
    overlay.querySelector('.concert-list-close')?.focus();
  }

  button.addEventListener('click', openPanel);
})();
