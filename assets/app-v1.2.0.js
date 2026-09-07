const citySelect = document.getElementById('citySelect');
const theaterSelect = document.getElementById('theaterSelect');
const yearSelect = document.getElementById('yearSelect');
const monthSelect = document.getElementById('monthSelect');
const weekdayGroup = document.getElementById('weekdayGroup');
const calendarScroller = document.getElementById('calendarScroller');
const summaryText = document.getElementById('summaryText');
const emptyState = document.getElementById('emptyState');
const todayButton = document.getElementById('todayButton');

const MONTH_NAMES = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
const WEEK_HEADERS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
const WEEK_OPTIONS = [
  { value: 1, label: '周一' }, { value: 2, label: '周二' }, { value: 3, label: '周三' },
  { value: 4, label: '周四' }, { value: 5, label: '周五' }, { value: 6, label: '周六' }, { value: 0, label: '周日' }
];
const STORAGE_KEY = 'concertdate.location-state.v1';
const now = new Date();

const THEATER_COLORS = {
  '杭州大剧院': '#22c55e',
  '杭州剧院': '#3b82f6',
  '浙江音乐厅': '#f59e0b',
  '杭州运河大剧院': '#a855f7',
  '临平大剧院': '#ef4444',
  '杭州金沙湖大剧院': '#06b6d4',
  '上海交响音乐厅': '#14b8a6',
  '上海东方艺术中心': '#f97316',
  '国家大剧院': '#6366f1',
  '北京音乐厅': '#ec4899'
};
const FALLBACK_COLORS = ['#22c55e', '#3b82f6', '#f59e0b', '#a855f7', '#ef4444', '#06b6d4', '#14b8a6', '#f97316'];

let data = { cities: [], concerts: [] };
let state = { city: 'all', theater: 'all', year: 'all', month: 'all', weekdays: [] };

function colorForTheater(name) {
  if (THEATER_COLORS[name]) return THEATER_COLORS[name];
  let hash = 0;
  for (const ch of String(name)) hash = ((hash << 5) - hash + ch.charCodeAt(0)) | 0;
  return FALLBACK_COLORS[Math.abs(hash) % FALLBACK_COLORS.length];
}

function readSavedLocation() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    if (saved && typeof saved === 'object') {
      state.city = saved.city ?? 'all';
      state.theater = saved.theater ?? 'all';
    }
  } catch {}
}

function saveLocation() {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify({ city: state.city, theater: state.theater })); } catch {}
}

readSavedLocation();
init();

async function init() {
  try {
    const response = await fetch('./data/concerts.json', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    data = await response.json();
    setupSelectors();
    attachListeners();
    renderCalendar();
    requestAnimationFrame(() => initialScroll());
  } catch (error) {
    calendarScroller.innerHTML = '<p class="empty-state">无法读取音乐会数据。</p>';
    console.error(error);
  }
}

function availableYears() {
  const years = new Set(data.concerts.map(item => Number(item.date.slice(0, 4))).filter(Number.isFinite));
  years.add(now.getFullYear());
  years.add(now.getFullYear() + 1);
  return [...years].sort((a, b) => a - b);
}

function setupSelectors() {
  citySelect.innerHTML = '<option value="all">全部城市</option>' + data.cities.map(({ name }) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join('');
  if (![...citySelect.options].some(o => o.value === state.city)) state.city = 'all';
  citySelect.value = state.city;
  updateTheaterOptions();

  const years = availableYears();
  yearSelect.innerHTML = '<option value="all">全部年份</option>' + years.map(year => `<option value="${year}">${year}年</option>`).join('');
  state.year = 'all';
  yearSelect.value = 'all';

  monthSelect.innerHTML = '<option value="all">全部月份</option>' + MONTH_NAMES.map((name, index) => `<option value="${index}">${name}</option>`).join('');
  state.month = 'all';
  monthSelect.value = 'all';

  state.weekdays = [];
  renderWeekdayDropdown();
  saveLocation();
}

function renderWeekdayDropdown() {
  weekdayGroup.innerHTML = `
    <button id="weekdayDropdownButton" class="weekday-dropdown-button" type="button" aria-expanded="false">
      <span id="weekdayDropdownLabel">全部星期</span><span class="weekday-chevron">⌄</span>
    </button>
    <div id="weekdayDropdownPanel" class="weekday-dropdown-panel" hidden>
      ${WEEK_OPTIONS.map(item => `<label class="weekday-check"><input type="checkbox" value="${item.value}"><span>${item.label}</span></label>`).join('')}
    </div>`;
}

function updateWeekdayLabel() {
  const label = document.getElementById('weekdayDropdownLabel');
  if (!label) return;
  label.textContent = state.weekdays.length
    ? state.weekdays.map(v => WEEK_OPTIONS.find(x => x.value === v)?.label).filter(Boolean).join('、')
    : '全部星期';
}

function theaterNamesForCurrentCity() {
  if (state.city === 'all') return [...new Set(data.cities.flatMap(city => city.theaters))];
  return data.cities.find(city => city.name === state.city)?.theaters || [];
}

function renderTheaterDropdown(theaters) {
  let shell = document.getElementById('theaterDropdownShell');
  if (!shell) {
    shell = document.createElement('div');
    shell.id = 'theaterDropdownShell';
    shell.className = 'theater-dropdown-shell';
    theaterSelect.insertAdjacentElement('afterend', shell);
    theaterSelect.classList.add('theater-native-select');
  }

  const selectedText = state.theater === 'all' ? '全部剧院' : state.theater;
  const selectedDot = state.theater === 'all' ? '' : `<span class="theater-color-dot" style="--theater-color:${colorForTheater(state.theater)}"></span>`;
  shell.innerHTML = `
    <button id="theaterDropdownButton" class="theater-dropdown-button" type="button" aria-expanded="false">
      <span class="theater-dropdown-value">${escapeHtml(selectedText)}${selectedDot}</span><span class="theater-chevron">⌄</span>
    </button>
    <div id="theaterDropdownPanel" class="theater-dropdown-panel" hidden>
      <button type="button" class="theater-option${state.theater === 'all' ? ' selected' : ''}" data-theater="all">全部剧院</button>
      ${theaters.map(name => `<button type="button" class="theater-option${state.theater === name ? ' selected' : ''}" data-theater="${escapeHtml(name)}"><span>${escapeHtml(name)}</span><span class="theater-color-dot" style="--theater-color:${colorForTheater(name)}"></span></button>`).join('')}
    </div>`;
}

function updateTheaterOptions() {
  const theaters = theaterNamesForCurrentCity();
  theaterSelect.innerHTML = '<option value="all">全部剧院</option>' + theaters.map(name => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join('');
  if (![...theaterSelect.options].some(o => o.value === state.theater)) state.theater = 'all';
  theaterSelect.value = state.theater;
  renderTheaterDropdown(theaters);
}

function closeCustomDropdowns(except = null) {
  if (except !== 'weekday') {
    const panel = document.getElementById('weekdayDropdownPanel');
    const button = document.getElementById('weekdayDropdownButton');
    if (panel) panel.hidden = true;
    if (button) button.setAttribute('aria-expanded', 'false');
  }
  if (except !== 'theater') {
    const panel = document.getElementById('theaterDropdownPanel');
    const button = document.getElementById('theaterDropdownButton');
    if (panel) panel.hidden = true;
    if (button) button.setAttribute('aria-expanded', 'false');
  }
}

function attachListeners() {
  citySelect.addEventListener('change', () => {
    state.city = citySelect.value;
    state.theater = 'all';
    updateTheaterOptions();
    saveLocation();
    renderCalendar();
  });

  theaterSelect.addEventListener('change', () => {
    state.theater = theaterSelect.value;
    saveLocation();
    renderTheaterDropdown(theaterNamesForCurrentCity());
    renderCalendar();
  });

  document.addEventListener('click', event => {
    const theaterButton = event.target.closest('#theaterDropdownButton');
    const theaterOption = event.target.closest('.theater-option');
    const weekdayButton = event.target.closest('#weekdayDropdownButton');

    if (theaterButton) {
      const panel = document.getElementById('theaterDropdownPanel');
      const opening = panel?.hidden ?? false;
      closeCustomDropdowns('theater');
      if (panel) panel.hidden = !opening;
      theaterButton.setAttribute('aria-expanded', String(opening));
      return;
    }

    if (theaterOption) {
      theaterSelect.value = theaterOption.dataset.theater;
      theaterSelect.dispatchEvent(new Event('change', { bubbles: true }));
      closeCustomDropdowns();
      return;
    }

    if (weekdayButton) {
      const panel = document.getElementById('weekdayDropdownPanel');
      const opening = panel?.hidden ?? false;
      closeCustomDropdowns('weekday');
      if (panel) panel.hidden = !opening;
      weekdayButton.setAttribute('aria-expanded', String(opening));
      return;
    }

    if (!event.target.closest('#weekdayDropdownPanel')) closeCustomDropdowns();
  });

  yearSelect.addEventListener('change', () => {
    state.year = yearSelect.value === 'all' ? 'all' : Number(yearSelect.value);
    renderCalendar();
    requestAnimationFrame(() => initialScroll(true));
  });

  monthSelect.addEventListener('change', () => {
    state.month = monthSelect.value === 'all' ? 'all' : Number(monthSelect.value);
    if (state.month !== 'all') requestAnimationFrame(() => scrollToMonth(state.month, true));
  });

  weekdayGroup.addEventListener('change', () => {
    state.weekdays = [...weekdayGroup.querySelectorAll('input:checked')].map(input => Number(input.value));
    updateWeekdayLabel();
    renderCalendar();
    requestAnimationFrame(() => initialScroll(false));
  });

  todayButton.addEventListener('click', () => {
    state.year = now.getFullYear();
    state.month = now.getMonth();
    yearSelect.value = String(state.year);
    monthSelect.value = String(state.month);
    renderCalendar();
    requestAnimationFrame(() => scrollToMonth(state.month, true, state.year));
  });
}

function eventMatches(item) {
  const parsed = parseDateOnly(item.date);
  if (state.city !== 'all' && item.city !== state.city) return false;
  if (state.theater !== 'all' && item.theater !== state.theater) return false;
  if (state.year !== 'all' && parsed.year !== Number(state.year)) return false;
  if (state.weekdays.length && !state.weekdays.includes(parsed.weekday)) return false;
  return true;
}

function renderCalendar() {
  const filteredConcerts = data.concerts.filter(eventMatches);
  const eventsByDate = new Map();
  for (const item of filteredConcerts) {
    if (!eventsByDate.has(item.date)) eventsByDate.set(item.date, []);
    eventsByDate.get(item.date).push(item);
  }
  const years = state.year === 'all' ? availableYears() : [Number(state.year)];
  calendarScroller.innerHTML = years.map(year => `<div class="year-block" data-year="${year}"><div class="year-heading">${year}年</div>${Array.from({ length: 12 }, (_, month) => renderMonth(year, month, eventsByDate)).join('')}</div>`).join('');
  const yearLabel = state.year === 'all' ? '全部年份' : `${state.year}年`;
  const weekdaysLabel = state.weekdays.length ? state.weekdays.map(v => WEEK_OPTIONS.find(x => x.value === v)?.label).filter(Boolean).join('、') : '全部星期';
  summaryText.textContent = `${yearLabel} · ${state.city === 'all' ? '全部城市' : state.city} · ${state.theater === 'all' ? '全部剧院' : state.theater} · ${weekdaysLabel} · ${filteredConcerts.length} 场`;
  emptyState.hidden = filteredConcerts.length !== 0;
}

function renderMonth(year, month, eventsByDate) {
  const firstDay = new Date(Date.UTC(year, month, 1));
  const daysInMonth = new Date(Date.UTC(year, month + 1, 0)).getUTCDate();
  const leadingBlankCount = (firstDay.getUTCDay() + 6) % 7;
  const blanks = Array.from({ length: leadingBlankCount }, () => '<div class="day empty" aria-hidden="true"></div>');
  const days = [];
  let monthConcertCount = 0;

  for (let day = 1; day <= daysInMonth; day++) {
    const dateString = formatDate(year, month + 1, day);
    const weekday = new Date(Date.UTC(year, month, day)).getUTCDay();
    const events = eventsByDate.get(dateString) || [];
    const hasConcert = events.length > 0;
    const weekdayMatches = !state.weekdays.length || state.weekdays.includes(weekday);
    const isToday = year === now.getFullYear() && month === now.getMonth() && day === now.getDate();
    monthConcertCount += events.length;

    const eventHtml = hasConcert
      ? `<div class="event-list theater-event-dots">${events.map(event => `<span class="concert-marker theater-concert-marker" style="--theater-color:${colorForTheater(event.theater)}" aria-hidden="true" title="${escapeHtml(event.theater)}"></span>`).join('')}</div>`
      : '';

    days.push(`<div class="day${hasConcert ? ' has-concert concert-clickable' : ''}${weekdayMatches ? '' : ' filtered-out'}${isToday ? ' today' : ''}" tabindex="${hasConcert ? '0' : '-1'}" data-date="${dateString}" aria-label="${year}年${month + 1}月${day}日，${hasConcert ? `有${events.length}场音乐会` : '无音乐会'}"><span class="day-number">${day}</span>${eventHtml}</div>`);
  }

  return `<section class="month-card" id="month-${year}-${month}" data-year="${year}" data-month="${month}"><div class="month-title"><h2>${MONTH_NAMES[month]}</h2><span>${monthConcertCount} 场音乐会</span></div><div class="week-header" aria-hidden="true">${WEEK_HEADERS.map(item => `<div>${item}</div>`).join('')}</div><div class="days-grid">${blanks.join('')}${days.join('')}</div></section>`;
}

function initialScroll(smooth = false) {
  if (state.month !== 'all') { scrollToMonth(Number(state.month), smooth); return; }
  if (state.year === 'all') scrollToMonth(now.getMonth(), smooth, now.getFullYear());
  else calendarScroller.scrollTo({ top: 0, behavior: smooth ? 'smooth' : 'auto' });
}

function scrollToMonth(month, smooth = true, preferredYear = null) {
  const years = state.year === 'all' ? availableYears() : [Number(state.year)];
  let targetYear = preferredYear ?? (state.year === 'all' && years.includes(now.getFullYear()) ? now.getFullYear() : years[0]);
  if (!years.includes(Number(targetYear))) targetYear = years[0];
  const target = document.getElementById(`month-${targetYear}-${month}`);
  if (!target) return;
  const top = target.offsetTop - calendarScroller.offsetTop;
  calendarScroller.scrollTo({ top: Math.max(0, top - 10), behavior: smooth ? 'smooth' : 'auto' });
}

function parseDateOnly(value) {
  const [year, month, day] = value.split('-').map(Number);
  return { year, month, day, weekday: new Date(Date.UTC(year, month - 1, day)).getUTCDay() };
}
function formatDate(year, month, day) { return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`; }
function escapeHtml(value) { return String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#039;'); }
window.refreshConcertData = freshData => { data = freshData; setupSelectors(); renderCalendar(); requestAnimationFrame(() => initialScroll(false)); };
