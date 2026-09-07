(() => {
  const DATA_URL = './data/concerts.json';
  const VERSION_URL = './data/version.json';
  const DATA_CACHE = 'concertdate-data-v1';
  const nativeFetch = window.fetch.bind(window);

  async function readCachedData() {
    if (!('caches' in window)) return null;
    try {
      const cache = await caches.open(DATA_CACHE);
      const cached = await cache.match(DATA_URL);
      return cached ? cached.clone() : null;
    } catch {
      return null;
    }
  }

  async function saveCachedData(response) {
    if (!('caches' in window) || !response?.ok) return;
    try {
      const cache = await caches.open(DATA_CACHE);
      await cache.put(DATA_URL, response.clone());
    } catch (error) {
      console.warn('Unable to cache concert data', error);
    }
  }

  window.fetch = async (input, init = {}) => {
    const requestUrl = typeof input === 'string' ? input : input.url;
    const absolute = new URL(requestUrl, location.href);

    if (absolute.pathname.endsWith('/data/concerts.json')) {
      const cached = await readCachedData();
      if (cached) return cached;

      const response = await nativeFetch(input, { ...init, cache: 'no-store' });
      await saveCachedData(response);
      return response;
    }

    return nativeFetch(input, init);
  };

  async function refreshFromRemoteIfNeeded() {
    try {
      const versionResponse = await nativeFetch(
        `${VERSION_URL}?t=${Date.now()}`,
        { cache: 'no-store' }
      );
      if (!versionResponse.ok) return;

      const remoteMeta = await versionResponse.json();
      const remoteVersion = remoteMeta?.version;
      const localVersion = typeof data !== 'undefined' ? data?.version : null;

      if (!remoteVersion || remoteVersion === localVersion) return;

      const freshResponse = await nativeFetch(
        `${DATA_URL}?v=${encodeURIComponent(remoteVersion)}`,
        { cache: 'no-store' }
      );
      if (!freshResponse.ok) return;

      const freshData = await freshResponse.json();

      if ('caches' in window) {
        const cache = await caches.open(DATA_CACHE);
        await cache.put(
          DATA_URL,
          new Response(JSON.stringify(freshData), {
            headers: { 'Content-Type': 'application/json; charset=utf-8' }
          })
        );
      }

      if (typeof data !== 'undefined') {
        data = freshData;
        setupSelectors();
        citySelect.value = state.city;
        theaterSelect.value = state.theater;
        yearSelect.value = String(state.year);
        monthSelect.value = String(state.month);
        weekdaySelect.value = state.weekday;
        renderCalendar();
        requestAnimationFrame(() => scrollToMonth(state.month, false));
      }
    } catch (error) {
      console.warn('Concert data version check failed', error);
    }
  }

  window.addEventListener('DOMContentLoaded', () => {
    setTimeout(refreshFromRemoteIfNeeded, 0);
  });
})();