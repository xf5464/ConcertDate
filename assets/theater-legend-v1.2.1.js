(() => {
  function visibleTheatersForLegend() {
    if (typeof state === 'undefined' || typeof data === 'undefined') return [];
    if (state.theater && state.theater !== 'all') return [state.theater];
    if (typeof theaterNamesForCurrentCity === 'function') return theaterNamesForCurrentCity();
    if (state.city && state.city !== 'all') {
      return data.cities.find(city => city.name === state.city)?.theaters || [];
    }
    return [...new Set(data.cities.flatMap(city => city.theaters || []))];
  }

  function legendHtml() {
    const theaters = visibleTheatersForLegend();
    if (!theaters.length) return '';
    return `<div class="year-theater-legend" aria-label="剧院颜色图例">${theaters.map(name => `
      <span class="year-theater-legend-item">
        <span class="year-theater-legend-dot" style="--theater-color:${colorForTheater(name)}" aria-hidden="true"></span>
        <span>${escapeHtml(name)}</span>
      </span>`).join('')}</div>`;
  }

  function injectTheaterLegends() {
    const html = legendHtml();
    document.querySelectorAll('.year-heading').forEach(heading => {
      heading.querySelector('.year-theater-legend')?.remove();
      if (html) heading.insertAdjacentHTML('afterbegin', html);
    });
  }

  if (typeof renderCalendar === 'function') {
    const originalRenderCalendar = renderCalendar;
    renderCalendar = function(...args) {
      const result = originalRenderCalendar.apply(this, args);
      injectTheaterLegends();
      return result;
    };
  }

  const observer = new MutationObserver(() => injectTheaterLegends());
  const scroller = document.getElementById('calendarScroller');
  if (scroller) observer.observe(scroller, { childList: true, subtree: false });
  requestAnimationFrame(injectTheaterLegends);
})();
