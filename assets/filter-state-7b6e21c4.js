(() => {
  const STORAGE_KEY = 'concertdate.filter-state.v1';
  const ids = ['citySelect', 'theaterSelect', 'yearSelect', 'monthSelect', 'weekdaySelect'];

  const readSaved = () => {
    try {
      const value = localStorage.getItem(STORAGE_KEY);
      return value ? JSON.parse(value) : {};
    } catch {
      return {};
    }
  };

  const saveCurrent = () => {
    try {
      const state = {};
      for (const id of ids) {
        const el = document.getElementById(id);
        if (el) state[id] = el.value;
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      // Ignore storage failures, for example private browsing quota restrictions.
    }
  };

  const hasOption = (select, value) =>
    [...select.options].some(option => option.value === String(value));

  const applyValue = (id, value) => {
    const select = document.getElementById(id);
    if (!select || value == null || !hasOption(select, value)) return false;
    select.value = String(value);
    select.dispatchEvent(new Event('change', { bubbles: true }));
    return true;
  };

  const selectorsReady = () => {
    const city = document.getElementById('citySelect');
    const year = document.getElementById('yearSelect');
    const month = document.getElementById('monthSelect');
    return city?.options.length > 0 && year?.options.length > 0 && month?.options.length > 0;
  };

  const restore = () => {
    if (!selectorsReady()) return false;

    const saved = readSaved();

    // Restore city first because it rebuilds the theater options synchronously.
    applyValue('citySelect', saved.citySelect);
    applyValue('theaterSelect', saved.theaterSelect);
    applyValue('yearSelect', saved.yearSelect);
    applyValue('monthSelect', saved.monthSelect);
    applyValue('weekdaySelect', saved.weekdaySelect);

    for (const id of ids) {
      document.getElementById(id)?.addEventListener('change', saveCurrent);
    }

    document.getElementById('todayButton')?.addEventListener('click', () => {
      setTimeout(saveCurrent, 0);
    });

    // Persist normalized values in case an old saved option no longer exists.
    saveCurrent();
    return true;
  };

  if (!restore()) {
    const timer = setInterval(() => {
      if (restore()) clearInterval(timer);
    }, 50);
    setTimeout(() => clearInterval(timer), 10000);
  }
})();
