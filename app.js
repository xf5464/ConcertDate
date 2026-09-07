const citySelect = document.getElementById('citySelect');
const theaterSelect = document.getElementById('theaterSelect');
const yearSelect = document.getElementById('yearSelect');
const monthSelect = document.getElementById('monthSelect');
const weekdaySelect = document.getElementById('weekdaySelect');
const calendarScroller = document.getElementById('calendarScroller');
const summaryText = document.getElementById('summaryText');
const emptyState = document.getElementById('emptyState');
const todayButton = document.getElementById('todayButton');

const MONTH_NAMES = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
const WEEK_HEADERS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
const now = new Date();

let data = { cities: [], concerts: [] };
let state = {
  city: 'all',
  theater: 'all',
  year: now.getFullYear(),
  month: now.getMonth(),
  weekday: 'all'
};

init();

async function init() {
  try {
    const response = await fetch('./data/concerts.json', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    data = await response.json();
    setupSelectors();
    attachListeners();
    renderCalendar();
    requestAnimationFrame(() => scrollToMonth(state.month, false));
  } catch (error) {
    calendarScroller.innerHTML = '<p class="empty-state">无法读取 data/concerts.json。请通过本地 HTTP 服务或 GitHub Pages 打开本项目。</p>';
    console.error(error);
  }
}

function setupSelectors() {
  citySelect.innerHTML = '<option value="all">全部城市</option>' +
    data.cities.map(({ name }) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join('');

  const years = new Set(data.concerts.map(item => Number(item.date.slice(0, 4))));
  years.add(now.getFullYear());
  years.add(now.getFullYear() + 1);

  yearSelect.innerHTML = [...years]
    .sort((a, b) => a - b)
    .map(year => `<option value="${year}">${year}年</option>`)
    .join('');

  if (!years.has(state.year)) state.year = [...years].sort((a, b) => a - b)[0];
  yearSelect.value = String(state.year);

  monthSelect.innerHTML = MONTH_NAMES
    .map((name, index) => `<option value="${index}">${name}</option>`)
    .join('');
  monthSelect.value = String(state.month);

  updateTheaterOptions();
}

function attachListeners() {
  citySelect.addEventListener('change', () => {
    state.city = citySelect.value;
    state.theater = 'all';
    updateTheaterOptions();
    renderCalendar();
  });

  theaterSelect.addEventListener('change', () => {
    state.theater = theaterSelect.value;
    renderCalendar();
  });

  yearSelect.addEventListener('change', () => {
    state.year = Number(yearSelect.value);
    renderCalendar();
    requestAnimationFrame(() => scrollToMonth(state.month));
  });

  monthSelect.addEventListener('change', () => {
    state.month = Number(monthSelect.value);
    scrollToMonth(state.month);
  });

  weekdaySelect.addEventListener('change', () => {
    state.weekday = weekdaySelect.value;
    renderCalendar();
    requestAnimationFrame(() => scrollToMonth(state.month, false));
  });

  todayButton.addEventListener('click', () => {
    const today = new Date();
    state.year = today.getFullYear();
    state.month = today.getMonth();

    if (![...yearSelect.options].some(option => Number(option.value) === state.year)) {
      const option = document.createElement('option');
      option.value = String(state.year);
      option.textContent = `${state.year}年`;
      yearSelect.appendChild(option);
    }

    yearSelect.value = String(state.year);
    monthSelect.value = String(state.month);
    renderCalendar();
    requestAnimationFrame(() => scrollToMonth(state.month));
  });
}

function updateTheaterOptions() {
  let theaters = [];

  if (state.city === 'all') {
    theaters = [...new Set(data.cities.flatMap(city => city.theaters))];
  } else {
    theaters = data.cities.find(city => city.name === state.city)?.theaters || [];
  }

  theaterSelect.innerHTML = '<option value="all">全部剧院</option>' +
    theaters.map(name => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join('');
  theaterSelect.value = state.theater;
}

function renderCalendar() {
  const filteredConcerts = data.concerts.filter(item => {
    const date = parseDateOnly(item.date);
    const cityMatches = state.city === 'all' || item.city === state.city;
    const theaterMatches = state.theater === 'all' || item.theater === state.theater;
    const yearMatches = date.year === state.year;
    const weekdayMatches = state.weekday === 'all' || date.weekday === Number(state.weekday);
    return cityMatches && theaterMatches && yearMatches && weekdayMatches;
  });

  const eventsByDate = new Map();
  for (const item of filteredConcerts) {
    if (!eventsByDate.has(item.date)) eventsByDate.set(item.date, []);
    eventsByDate.get(item.date).push(item);
  }

  calendarScroller.innerHTML = Array.from({ length: 12 }, (_, month) =>
    renderMonth(state.year, month, eventsByDate)
  ).join('');

  const scope = [
    state.city === 'all' ? '全部城市' : state.city,
    state.theater === 'all' ? '全部剧院' : state.theater,
    `${filteredConcerts.length} 场`
  ].join(' · ');

  summaryText.textContent = `${state.year}年 · ${scope}`;
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
    const utcDate = new Date(Date.UTC(year, month, day));
    const weekday = utcDate.getUTCDay();
    const events = eventsByDate.get(dateString) || [];
    const hasConcert = events.length > 0;
    const weekdayMatches = state.weekday === 'all' || weekday === Number(state.weekday);
    const isToday = year === now.getFullYear() && month === now.getMonth() && day === now.getDate();

    monthConcertCount += events.length;

    const eventHtml = events.length
      ? `<div class="event-list">${events.map(event => `<span class="event-chip" title="${escapeHtml(event.title)} · ${escapeHtml(event.theater)}">${escapeHtml(event.title)}</span>`).join('')}</div>`
      : '<span class="no-event-mark" aria-hidden="true"></span>';

    days.push(`
      <div class="day${hasConcert ? ' has-concert' : ''}${weekdayMatches ? '' : ' filtered-out'}${isToday ? ' today' : ''}"
           tabindex="0"
           aria-label="${year}年${month + 1}月${day}日，${hasConcert ? `有${events.length}场音乐会` : '无音乐会'}">
        <span class="day-number">${day}</span>
        ${eventHtml}
      </div>
    `);
  }

  return `
    <section class="month-card" id="month-${month}" data-month="${month}">
      <div class="month-title">
        <h2>${MONTH_NAMES[month]}</h2>
        <span>${monthConcertCount} 场音乐会</span>
      </div>
      <div class="week-header" aria-hidden="true">
        ${WEEK_HEADERS.map(item => `<div>${item}</div>`).join('')}
      </div>
      <div class="days-grid">
        ${blanks.join('')}${days.join('')}
      </div>
    </section>
  `;
}

function scrollToMonth(month, smooth = true) {
  const target = document.getElementById(`month-${month}`);
  if (!target) return;

  const top = target.offsetTop - calendarScroller.offsetTop;
  calendarScroller.scrollTo({
    top: Math.max(0, top - 10),
    behavior: smooth ? 'smooth' : 'auto'
  });
}

function parseDateOnly(value) {
  const [year, month, day] = value.split('-').map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  return {
    year,
    month,
    day,
    weekday: date.getUTCDay()
  };
}

function formatDate(year, month, day) {
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}
