import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "concerts.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ConcertDateBot/1.0; +https://github.com/xf5464/ConcertDate)"
}
TIMEOUT = 20

VENUES = [
    {"city": "杭州", "theater": "杭州大剧院"},
    {"city": "杭州", "theater": "杭州剧院"},
    {"city": "上海", "theater": "上海交响音乐厅"},
    {"city": "上海", "theater": "上海东方艺术中心"},
    {"city": "北京", "theater": "国家大剧院"},
    {"city": "北京", "theater": "北京音乐厅"},
]


def fetch(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding
    return response.text


def normalize_title(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" -｜|·\n\t")


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


def scrape_beijing_concert_hall() -> list[dict]:
    url = "https://www.bjconcerthall.cn/bjyyt/ycgp/ycgp.shtml"
    soup = BeautifulSoup(fetch(url), "html.parser")
    events: list[dict] = []

    # The listing page is server-rendered. Search each event-like block for
    # a YYYY-MM-DD date and a meaningful title.
    for block in soup.find_all(["li", "div", "article"]):
        text = normalize_title(block.get_text(" ", strip=True))
        match = re.search(r"(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})", text)
        if not match:
            continue
        date_str = f"{int(match.group(1)):04d}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
        if not valid_future_or_recent(date_str):
            continue

        title_node = block.find(["h1", "h2", "h3", "h4", "a"])
        title = normalize_title(title_node.get_text(" ", strip=True)) if title_node else ""
        if not title or len(title) < 4 or "购票" == title:
            # Fallback: take text preceding the date, stripping common labels.
            prefix = text[: match.start()].strip()
            prefix = re.sub(r"^(立即购票|查看更多|演出购票)+", "", prefix).strip()
            title = prefix[-100:].strip()
        if title:
            events.append(make_event(date_str, "北京", "北京音乐厅", title, url))

    return dedupe(events)


def scrape_hangzhou_theater() -> list[dict]:
    # Zhejiang Performing Arts Group's venue-management site includes Hangzhou Theatre listings.
    url = "https://www.zjyy99.com/Home/Article/listZxdp/menu_id/24/leibie_id/7"
    soup = BeautifulSoup(fetch(url), "html.parser")
    events: list[dict] = []

    for block in soup.find_all(["li", "div", "article"]):
        text = normalize_title(block.get_text(" ", strip=True))
        if "杭州剧院" not in text:
            continue
        # Only keep concert-like performances; this app is not a generic theatre calendar.
        if not any(k in text for k in ("音乐", "交响", "钢琴", "小提琴", "室内乐", "乐团", "独奏", "合唱")):
            continue
        match = re.search(r"(20\d{2})[./-](\d{1,2})[./-](\d{1,2})", text)
        if not match:
            continue
        date_str = f"{int(match.group(1)):04d}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
        if not valid_future_or_recent(date_str):
            continue
        title_node = block.find(["h1", "h2", "h3", "h4", "a"])
        title = normalize_title(title_node.get_text(" ", strip=True)) if title_node else ""
        if not title or title == "杭州剧院":
            title = text.split("杭州剧院", 1)[0].strip()
        if title:
            events.append(make_event(date_str, "杭州", "杭州剧院", title, url))

    return dedupe(events)


def scrape_shanghai_symphony_hall() -> list[dict]:
    # Shanghai Concerts is a public, independently edited classical-concert calendar.
    # It is used here because it exposes a stable, server-rendered venue calendar.
    url = "https://shanghaiconcerts.com/concerts?venue=ssh-concert-hall"
    soup = BeautifulSoup(fetch(url), "html.parser")
    events: list[dict] = []

    # Parse compact event sections: title, then a nearby yyyy/mm/day or Chinese month/day context.
    full_text = soup.get_text("\n", strip=True)
    current_year = date.today().year
    current_month = None
    lines = [normalize_title(x) for x in full_text.splitlines() if normalize_title(x)]

    for i, line in enumerate(lines):
        month_match = re.search(r"(20\d{2})年(\d{1,2})月", line)
        if month_match:
            current_year = int(month_match.group(1))
            current_month = int(month_match.group(2))
            continue
        if current_month is None:
            continue

        day_match = re.search(r"(?:周[一二三四五六日天])?(\d{1,2})$", line)
        if not day_match:
            continue
        day = int(day_match.group(1))
        if not 1 <= day <= 31:
            continue

        # The title generally follows the day line within the next few text nodes.
        title = ""
        for candidate in lines[i + 1 : i + 5]:
            if len(candidate) >= 5 and not re.match(r"^(周[一二三四五六日天]|\d{1,2}:\d{2}|¥|上海交响乐团音乐厅)", candidate):
                title = candidate
                break
        if not title:
            continue
        try:
            date_str = date(current_year, current_month, day).isoformat()
        except ValueError:
            continue
        if valid_future_or_recent(date_str):
            events.append(make_event(date_str, "上海", "上海交响音乐厅", title, url))

    return dedupe(events)


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


def build_cities() -> list[dict]:
    cities: dict[str, list[str]] = {}
    for item in VENUES:
        cities.setdefault(item["city"], []).append(item["theater"])
    return [{"name": city, "theaters": theaters} for city, theaters in cities.items()]


def main():
    scrapers = [
        ("北京音乐厅", scrape_beijing_concert_hall),
        ("杭州剧院", scrape_hangzhou_theater),
        ("上海交响音乐厅", scrape_shanghai_symphony_hall),
    ]

    events: list[dict] = []
    status: list[dict] = []
    for name, scraper in scrapers:
        try:
            items = scraper()
            events.extend(items)
            status.append({"source": name, "ok": True, "count": len(items)})
            print(f"[ok] {name}: {len(items)} events")
        except Exception as exc:
            status.append({"source": name, "ok": False, "count": 0, "error": str(exc)[:300]})
            print(f"[error] {name}: {exc}")

    # Never overwrite valid data with a completely empty result caused by upstream failures.
    if not events:
        raise RuntimeError("All active scrapers returned zero events; keeping the previous data file.")

    events = dedupe(events)
    events.sort(key=lambda e: (e["date"], e["city"], e["theater"], e["title"]))
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
