import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "concerts.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ConcertDateBot/1.0; +https://github.com/xf5464/ConcertDate)"
}
TIMEOUT = 25

VENUES = [
    {"city": "杭州", "theater": "杭州大剧院"},
    {"city": "杭州", "theater": "杭州剧院"},
    {"city": "上海", "theater": "上海交响音乐厅"},
    {"city": "上海", "theater": "上海东方艺术中心"},
    {"city": "北京", "theater": "国家大剧院"},
    {"city": "北京", "theater": "北京音乐厅"},
]

CONCERT_KEYWORDS = (
    "音乐会", "交响", "管弦乐", "管风琴", "钢琴", "小提琴", "大提琴",
    "室内乐", "弦乐", "乐团", "独奏", "协奏", "合唱", "古典音乐",
    "交响乐", "爵士音乐会", "recital", "orchestra", "symphony",
)

NON_CONCERT_KEYWORDS = (
    "音乐剧", "音乐戏剧", "舞剧", "舞蹈", "脱口秀", "话剧", "戏曲",
    "儿童剧", "舞台剧", "芭蕾舞剧", "演唱会",
)


def fetch(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    if not response.encoding or response.encoding.lower() == "iso-8859-1":
        response.encoding = response.apparent_encoding or "utf-8"
    return response.text


def normalize_title(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" -｜|·\n\t")


def is_concert(text: str) -> bool:
    value = normalize_title(text).lower()
    if any(k.lower() in value for k in NON_CONCERT_KEYWORDS):
        return False
    return any(k.lower() in value for k in CONCERT_KEYWORDS)


def make_event(date_str: str, city: str, theater: str, title: str, source: str):
    return {
        "date": date_str,
        "city": city,
        "theater": theater,
        "title": normalize_title(title),
        "source": source,
    }


def valid_future_or_recent(date_str: str) -> bool:
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return False
    return d >= date.today().replace(day=1)


def infer_year(month: int) -> int:
    today = date.today()
    # A month far behind the current month is assumed to belong to next year.
    if month < today.month - 4:
        return today.year + 1
    return today.year


def parse_date_strings(text: str) -> list[str]:
    """Parse common Chinese event date formats and expand explicit date ranges."""
    text = normalize_title(text)

    # 2026/09/24 - 2026/09/27 (also accepts . and - separators)
    range_match = re.search(
        r"(20\d{2})[./-](\d{1,2})[./-](\d{1,2})\s*(?:-|—|–|至|~|～)\s*"
        r"(20\d{2})[./-](\d{1,2})[./-](\d{1,2})",
        text,
    )
    if range_match:
        try:
            start = date(int(range_match.group(1)), int(range_match.group(2)), int(range_match.group(3)))
            end = date(int(range_match.group(4)), int(range_match.group(5)), int(range_match.group(6)))
        except ValueError:
            return []
        if end < start or (end - start).days > 31:
            return []
        return [(start + timedelta(days=i)).isoformat() for i in range((end - start).days + 1)]

    # 2026.09.25 / 2026-09-25 / 2026/09/25
    match = re.search(r"(20\d{2})[./-](\d{1,2})[./-](\d{1,2})", text)
    if match:
        try:
            return [date(int(match.group(1)), int(match.group(2)), int(match.group(3))).isoformat()]
        except ValueError:
            return []

    # 2026年9月25日
    match = re.search(r"(20\d{2})年\s*(\d{1,2})月\s*(\d{1,2})日?", text)
    if match:
        try:
            return [date(int(match.group(1)), int(match.group(2)), int(match.group(3))).isoformat()]
        except ValueError:
            return []

    # 9/25 周五 19:30 or 9月25日
    match = re.search(r"(?<!\d)(\d{1,2})(?:/|月)(\d{1,2})(?:日)?(?!\d)", text)
    if match:
        month, day_num = int(match.group(1)), int(match.group(2))
        try:
            return [date(infer_year(month), month, day_num).isoformat()]
        except ValueError:
            return []

    return []


def dedupe(events: Iterable[dict]) -> list[dict]:
    seen = set()
    result = []
    for event in events:
        key = (event["date"], event["city"], event["theater"], event["title"])
        if key in seen:
            continue
        seen.add(key)
        result.append(event)
    return result


def scrape_hangzhou_grand_theater() -> list[dict]:
    """Hangzhou Grand Theatre upcoming-event calendar.

    The theatre's public website/index is not consistently crawlable, so this
    scraper uses the server-rendered venue calendar as the current discovery
    source. It only keeps concert-like events and records the source URL.
    """
    url = "https://localhub.to/hangzhou/venue/hangzhou-grand-theater?lang=zh"
    soup = BeautifulSoup(fetch(url), "html.parser")
    events: list[dict] = []

    headings = soup.find_all(["h2", "h3", "h4", "h5"])
    for heading in headings:
        title = normalize_title(heading.get_text(" ", strip=True))
        if not title or not is_concert(title):
            continue

        # Event cards vary slightly over time. Read the heading's closest card-like
        # parent, then fall back to nearby siblings if needed.
        context = heading
        for _ in range(4):
            if context.parent is None:
                break
            context = context.parent
            context_text = normalize_title(context.get_text(" ", strip=True))
            if "杭州大剧院" in context_text and parse_date_strings(context_text):
                break

        context_text = normalize_title(context.get_text(" ", strip=True))
        dates = parse_date_strings(context_text)
        for date_str in dates:
            if valid_future_or_recent(date_str):
                events.append(make_event(date_str, "杭州", "杭州大剧院", title, url))

    # Defensive fallback for markup where event titles are links instead of headings.
    if not events:
        for node in soup.find_all("a"):
            title = normalize_title(node.get_text(" ", strip=True))
            if len(title) < 5 or not is_concert(title):
                continue
            parent = node.parent
            for _ in range(4):
                if parent is None:
                    break
                text = normalize_title(parent.get_text(" ", strip=True))
                dates = parse_date_strings(text)
                if "杭州大剧院" in text and dates:
                    for date_str in dates:
                        if valid_future_or_recent(date_str):
                            events.append(make_event(date_str, "杭州", "杭州大剧院", title, url))
                    break
                parent = parent.parent

    return dedupe(events)


def scrape_hangzhou_theater() -> list[dict]:
    """Scrape Hangzhou Theatre from Zhejiang Performing Arts Group's official ticket page."""
    url = "https://zjyy99.com/listZxdp/24.html"
    soup = BeautifulSoup(fetch(url), "html.parser")
    events: list[dict] = []

    # Event cards contain title, venue and date together. We intentionally scan
    # several semantic/container elements because the site has changed templates.
    for block in soup.find_all(["li", "div", "article", "tr"]):
        text = normalize_title(block.get_text(" ", strip=True))
        if "杭州剧院" not in text or not is_concert(text):
            continue
        dates = parse_date_strings(text)
        if not dates:
            continue

        title = ""
        for node in block.find_all(["a", "h1", "h2", "h3", "h4"], limit=8):
            candidate = normalize_title(node.get_text(" ", strip=True))
            if candidate and candidate != "杭州剧院" and is_concert(candidate):
                title = candidate
                break

        if not title:
            # Trim everything from venue/date metadata onward.
            title = text.split("杭州剧院", 1)[0].strip()
        if not title or not is_concert(title):
            continue

        for date_str in dates:
            if valid_future_or_recent(date_str):
                events.append(make_event(date_str, "杭州", "杭州剧院", title, url))

    return dedupe(events)


def build_cities() -> list[dict]:
    cities: dict[str, list[str]] = {}
    for item in VENUES:
        cities.setdefault(item["city"], []).append(item["theater"])
    return [{"name": city, "theaters": theaters} for city, theaters in cities.items()]


def load_previous() -> dict:
    if not OUT.exists():
        return {"concerts": []}
    try:
        return json.loads(OUT.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"concerts": []}


def main():
    # Only Hangzhou is enabled for production scraping for now. Other cities stay
    # in the UI list and can be activated after their sources are verified.
    scrapers = [
        ("杭州大剧院", scrape_hangzhou_grand_theater),
        ("杭州剧院", scrape_hangzhou_theater),
    ]

    previous = load_previous()
    previous_events = previous.get("concerts", [])
    fresh_by_theater: dict[str, list[dict]] = {}
    status: list[dict] = []

    for theater, scraper in scrapers:
        try:
            items = dedupe(scraper())
            # Zero results is treated as suspicious rather than authoritative;
            # this prevents a temporary upstream/template problem from erasing data.
            if not items:
                raise RuntimeError("source returned zero concert events")
            fresh_by_theater[theater] = items
            status.append({"source": theater, "ok": True, "count": len(items)})
            print(f"[ok] {theater}: {len(items)} events")
        except Exception as exc:
            status.append({"source": theater, "ok": False, "count": 0, "error": str(exc)[:300]})
            print(f"[error] {theater}: {exc}")

    active_theaters = {name for name, _ in scrapers}
    events: list[dict] = []

    # Preserve unrelated cities and preserve the last known data for a Hangzhou
    # venue whose scraper failed during this run.
    for event in previous_events:
        theater = event.get("theater")
        if theater not in active_theaters:
            events.append(event)
        elif theater not in fresh_by_theater and valid_future_or_recent(event.get("date", "")):
            events.append(event)

    for items in fresh_by_theater.values():
        events.extend(items)

    events = dedupe(events)
    events.sort(key=lambda e: (e["date"], e["city"], e["theater"], e["title"]))

    # If both sources fail and there is no retained data, fail the workflow instead
    # of committing an empty calendar.
    if not events:
        raise RuntimeError("No valid concert data available; keeping the previous file.")

    payload = {
        "updatedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "cities": build_cities(),
        "concerts": events,
        "sources": status,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(events)} concerts to {OUT}")


if __name__ == "__main__":
    main()
