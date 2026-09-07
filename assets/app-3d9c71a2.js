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
  { value: 1, label: '一' }, { value: 2, label: '二' }, { value: 3, label: '三' },
  { value: 4, label: '四' }, { value: 5, label: '五' }, { value: 6, label: '六' }, { value: 0, label: '日' }
];
const STORAGE_KEY = 'concertdate.filter-state.v2';
const now = new Date();

let data = { cities: [], concerts: [] };
let state = {
  city: 'all',
  theater: 'all',
  year: 'all',
  month: 'all',
  weekdays: []
};

function readSavedState() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    if (saved && typeof saved === 'object') {
      state.city = saved.city ?? state.city;
      state.theater = saved.theater ?? state.theater;
      state.year = saved.year ?? state.year;
      state.month = saved.month ?? state.month;
      state.weekdays = Array.isArray(saved.weekdays) ? saved.weekdays.map(Number).filter(v => v >= 0 && v <= 6) : [];
    }
  } catch {}
}

function saveState() {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch {}
}

readSavedState();
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
  citySelect.innerHTML = '<option value="all">全部城市</option>' +
    data.cities.map(({ name }) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join('');
  if (![...citySelect.options].some(o => o.value === state.city)) state.city = 'all';
  citySelect.value = state.city;
  updateTheaterOptions();

  const years = availableYears();
  yearSelect.innerHTML = '<option value="all">全部年份</option>' +
    years.map(year => `<option value="${year}">${year}年</option>`).join('');
  if (state.year !== 'all' && !years.includes(Number(state.year))) state.year = 'all';
  yearSelect.value = String(state.year);

  monthSelect.innerHTML = '<option value="all">全部月份</option>' +
    MONTH_NAMES.map((name, index) => `<option value="${index}">${name}</option>`).join('');
  if (state.month !== 'all' && (Number(state.month) < 0 || Number(state.month) > 11)) state.month = 'all';
  monthSelect.value = String(state.month);

  weekdayGroup.innerHTML = WEEK_OPTIONS.map(item => `
    <label class="weekday-option">
      <input type="checkbox" value="${item.value}" ${state.weekdays.includes(item.value) ? 'checked' : ''} />
      <span>${item.label}</span>
    </label>`).join('');
  saveState();
}

function attachListeners() {
  citySelect.addEventListener('change', () => {
    state.city = citySelect.value;
    state.theater = 'all';
    updateTheaterOptions();
    saveState();
    renderCalendar();
  });

  theaterSelect.addEventListener('change', () => {
    state.theater = theaterSelect.value;
    saveState();
    renderCalendar();
  });

  yearSelect.addEventListener('change', () => {
    state.year = yearSelect.value === 'all' ? 'all' : Number(yearSelect.value);
    saveState();
    renderCalendar();
    requestAnimationFrame(() => initialScroll(true));
  });

  monthSelect.addEventListener('change', () => {
    state.month = monthSelect.value === 'all' ? 'all' : Number(monthSelect.value);
    saveState();
    if (state.month !== 'all') requestAnimationFrame(() => scrollToMonth(state.month, true));
  });

  weekdayGroup.addEventListener('change', () => {
    state.weekdays = [...weekdayGroup.querySelectorAll('input:checked')].map(input => Number(input.value));
    saveState();
    renderCalendar();
    requestAnimationFrame(() => initialScroll(false));
  });

  todayButton.addEventListener('click', () => {
    state.year = now.getFullYear();
    state.month = now.getMonth();
    yearSelect.value = String(state.year);
    monthSelect.value = String(state.month);
    saveState();
    renderCalendar();
    requestAnimationFrame(() => scrollToMonth(state.month, true, state.year));
  });
}

function updateTheaterOptions() {
  let theaters = [];
  if (state.city === 'all') theaters = [...new Set(data.cities.flatMap(city => city.theaters))];
  else theaters = data.cities.find(city => city.name === state.city)?.theaters || [];

  theaterSelect.innerHTML = '<option value="all">全部剧院</option>' +
    theaters.map(name => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join('');
  if (![...theaterSelect.options].some(o => o.value === state.theater)) state.theater = 'all';
  theaterSelect.value = state.theater;
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
  calendarScroller.innerHTML = years.map(year => `
    <div class="year-block" data-year="${year}">
      <div class="year-heading">${year}年</div>
      ${Array.from({ length: 12 }, (_, month) => renderMonth(year, month, eventsByDate)).join('')}
    </div>`).join('');

  const yearLabel = state.year === 'all' ? '全部年份' : `${state.year}年`;
  const weekdaysLabel = state.weekdays.length ? state.weekdays.map(v => WEEK_OPTIONS.find(x => x.value === v)?.label).filter(Boolean).map(v => `周${v}`).join('、') : '全部星期';
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
      ? '<div class="event-list"><span class="concert-marker" aria-hidden="true"></span></div>'
      : '';

    days.push(`
      <div class="day${hasConcert ? ' has-concert concert-clickable' : ''}${weekdayMatches ? '' : ' filtered-out'}${isToday ? ' today' : ''}"
           tabindex="${hasConcert ? '0' : '-1'}" data-date="${dateString}"
           aria-label="${year}年${month + 1}月${day}日，${hasConcert ? `有${events.length}场音乐会` : '无音乐会'}">
        <span class="day-number">${day}</span>${eventHtml}
      </div>`);
  }

  return `
    <section class="month-card" id="month-${year}-${month}" data-year="${year}" data-month="${month}">
      <div class="month-title"><h2>${MONTH_NAMES[month]}</h2><span>${monthConcertCount} 场音乐会</span></div>
      <div class="week-header" aria-hidden="true">${WEEK_HEADERS.map(item => `<div>${item}</div>`).join('')}</div>
      <div class="days-grid">${blanks.join('')}${days.join('')}</div>
    </section>`;
}

function initialScroll(smooth = false) {
  if (state.month !== 'all') {
    scrollToMonth(Number(state.month), smooth);
    return;
  }
  if (state.year === 'all') {
    scrollToMonth(now.getMonth(), smooth, now.getFullYear());
  } else {
    calendarScroller.scrollTo({ top: 0, behavior: smooth ? 'smooth' : 'auto' });
  }
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

function formatDate(year, month, day) {
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

function escapeHtml(value) {
  return String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#039;');
}

window.refreshConcertData = freshData => {
  data = freshData;
  setupSelectors();
  renderCalendar();
  requestAnimationFrame(() => initialScroll(false));
};
