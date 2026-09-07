import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

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
    {"city": "杭州", "theater": "浙江音乐厅"},
    {"city": "杭州", "theater": "杭州运河大剧院"},
    {"city": "杭州", "theater": "临平大剧院"},
    {"city": "杭州", "theater": "杭州金沙湖大剧院"},
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


def parse_start_time(text: str) -> str | None:
    value = normalize_title(text)
    # Prefer explicit HH:MM. Avoid treating years/dates as times.
    match = re.search(r"(?<!\d)([01]?\d|2[0-3])[:：]([0-5]\d)(?!\d)", value)
    if not match:
        return None
    return f"{int(match.group(1)):02d}:{match.group(2)}"


def parse_duration(text: str) -> tuple[int | None, str | None]:
    value = normalize_title(text)
    # Only keep duration when the source explicitly states it. Never infer.
    patterns = [
        r"(?:演出时长|演出时间|时长|全长|约)[:：\s]*约?\s*(\d{2,3})\s*分钟",
        r"约\s*(\d{2,3})\s*分钟",
        r"(\d{2,3})\s*分钟(?:左右|约)?",
    ]
    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            minutes = int(match.group(1))
            if 20 <= minutes <= 360:
                return minutes, f"约{minutes}分钟" if "约" in match.group(0) else f"{minutes}分钟"
    return None, None


def is_concert(text: str) -> bool:
    value = normalize_title(text).lower()
    if any(k.lower() in value for k in NON_CONCERT_KEYWORDS):
        return False
    return any(k.lower() in value for k in CONCERT_KEYWORDS)


def make_event(date_str: str, city: str, theater: str, title: str, source: str, raw_text: str = "", start_time: str | None = None):
    event = {
        "date": date_str,
        "city": city,
        "theater": theater,
        "title": normalize_title(title),
        "source": source,
    }
    source_text = raw_text or title
    parsed_time = start_time or parse_start_time(source_text)
    if parsed_time:
        event["startTime"] = parsed_time
    duration_minutes, duration_text = parse_duration(source_text)
    if duration_minutes is not None:
        event["durationMinutes"] = duration_minutes
    if duration_text:
        event["durationText"] = duration_text
    return event


def valid_future_or_recent(date_str: str) -> bool:
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return False
    return d >= date.today().replace(day=1)


def infer_year(text: str, month: int, day_num: int) -> int:
    """Infer a missing year without inventing a future performance.

    If the card/title explicitly contains the current year, trust that before
    weekday inference. This prevents titles such as `2026杭州… 4/18` from being
    shifted into 2027 merely because a nearby weekday string happens to match.
    """
    today = date.today()

    if str(today.year) in text:
        return today.year

    weekday_match = re.search(r"周([一二三四五六日天])", text)
    weekday_map = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6}

    if weekday_match:
        expected = weekday_map[weekday_match.group(1)]
        for year in (today.year, today.year + 1, today.year - 1):
            try:
                candidate = date(year, month, day_num)
            except ValueError:
                continue
            if candidate.weekday() == expected:
                return year

    return today.year


def parse_date_strings(text: str) -> list[str]:
    text = normalize_title(text)

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

    match = re.search(r"(20\d{2})[./-](\d{1,2})[./-](\d{1,2})", text)
    if match:
        try:
            return [date(int(match.group(1)), int(match.group(2)), int(match.group(3))).isoformat()]
        except ValueError:
            return []

    match = re.search(r"(20\d{2})年\s*(\d{1,2})月\s*(\d{1,2})日?", text)
    if match:
        try:
            return [date(int(match.group(1)), int(match.group(2)), int(match.group(3))).isoformat()]
        except ValueError:
            return []

    match = re.search(r"(?<!\d)(\d{1,2})\s*(?:/|月)\s*(\d{1,2})(?:日)?(?!\d)", text)
    if match:
        month, day_num = int(match.group(1)), int(match.group(2))
        try:
            return [date(infer_year(text, month, day_num), month, day_num).isoformat()]
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


def scrape_localhub_venue(theater: str, url: str, aliases: tuple[str, ...] = ()) -> list[dict]:
    soup = BeautifulSoup(fetch(url), "html.parser")
    events: list[dict] = []
    venue_tokens = (theater,) + aliases

    for heading in soup.find_all(["h2", "h3", "h4", "h5"]):
        title = normalize_title(heading.get_text(" ", strip=True))
        if not title or not is_concert(title):
            continue

        context = heading
        for _ in range(5):
            if context.parent is None:
                break
            context = context.parent
            text = normalize_title(context.get_text(" ", strip=True))
            if parse_date_strings(text) and any(token in text for token in venue_tokens):
                break

        text = normalize_title(context.get_text(" ", strip=True))
        if not any(token in text for token in venue_tokens):
            continue
        for date_str in parse_date_strings(text):
            if valid_future_or_recent(date_str):
                events.append(make_event(date_str, "杭州", theater, title, url, raw_text=text))

    if not events:
        for node in soup.find_all("a"):
            title = normalize_title(node.get_text(" ", strip=True))
            if len(title) < 5 or not is_concert(title):
                continue
            parent = node.parent
            for _ in range(5):
                if parent is None:
                    break
                text = normalize_title(parent.get_text(" ", strip=True))
                dates = parse_date_strings(text)
                if dates and any(token in text for token in venue_tokens):
                    for date_str in dates:
                        if valid_future_or_recent(date_str):
                            events.append(make_event(date_str, "杭州", theater, title, url, raw_text=text))
                    break
                parent = parent.parent

    return dedupe(events)


def scrape_hangzhou_grand_theater() -> list[dict]:
    return scrape_localhub_venue(
        "杭州大剧院",
        "https://localhub.to/hangzhou/venue/hangzhou-grand-theater?lang=zh",
    )


def scrape_hangzhou_theater() -> list[dict]:
    return scrape_localhub_venue(
        "杭州剧院",
        "https://localhub.to/hangzhou/venue/hangzhou-theater?lang=zh",
    )



def scrape_zhejiang_official_venue(theater: str) -> list[dict]:
    """Official-source-first scraper for Zhejiang Music Hall / Hangzhou Canal Grand Theatre.

    Priority:
    1) Zhejiang Performing Arts Group official ticket page (broad venue coverage)
    2) Zhejiang Symphony Orchestra official calendar (orchestral concerts)
    The caller may fall back to LocalHub only when both official sources return zero.
    """
    events: list[dict] = []

    # Official ticket platform operated by Zhejiang Performing Arts Group.
    ticket_url = "https://localhub.to/hangzhou/venue/hangzhou-theater?lang=zh"
    try:
        soup = BeautifulSoup(fetch(ticket_url), "html.parser")
        for block in soup.find_all(["li", "article", "tr", "div"]):
            raw = normalize_title(block.get_text(" ", strip=True))
            if theater not in raw or not is_concert(raw):
                continue

            # Official ticket cards include an explicit YYYY.MM.DD style date.
            dates = parse_date_strings(raw)
            if not dates:
                continue

            title = ""
            for node in block.find_all(["a", "h1", "h2", "h3", "h4"], limit=10):
                candidate = normalize_title(node.get_text(" ", strip=True))
                if candidate and candidate != theater and is_concert(candidate):
                    title = candidate
                    break
            if not title:
                # Remove venue/date/price metadata from the card text as a last resort.
                title = raw.split(theater, 1)[0].strip()
            if not title or not is_concert(title):
                continue

            source = ticket_url
            link = block.find("a", href=True)
            if link:
                source = urljoin(ticket_url, link.get("href"))

            for date_str in dates:
                if valid_future_or_recent(date_str):
                    events.append(make_event(date_str, "杭州", theater, title, source, raw_text=raw))
    except Exception as exc:
        print(f"[warn] zjyy99 official source for {theater}: {exc}")

    # Zhejiang Symphony Orchestra official event calendar. This is especially
    # useful for concerts at Hangzhou Canal Grand Theatre and Zhejiang Music Hall.
    orchestra_url = "https://www.zjso.org/yugao/"
    try:
        soup = BeautifulSoup(fetch(orchestra_url), "html.parser")
        for time_node in soup.find_all("time", attrs={"datetime": True}):
            raw_dt = str(time_node.get("datetime") or "")
            date_str = raw_dt[:10]
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                continue
            if not valid_future_or_recent(date_str):
                continue

            context = time_node
            for _ in range(7):
                if context.parent is None:
                    break
                context = context.parent
                context_text = normalize_title(context.get_text(" ", strip=True))
                if theater in context_text:
                    break

            context_text = normalize_title(context.get_text(" ", strip=True))
            if theater not in context_text:
                continue

            title = ""
            title_link = None
            for node in context.find_all(["h2", "h3", "h4", "a"], limit=12):
                candidate = normalize_title(node.get_text(" ", strip=True))
                if candidate and candidate != theater and is_concert(candidate):
                    title = candidate
                    if node.name == "a" and node.get("href"):
                        title_link = node
                    else:
                        title_link = node.find("a", href=True)
                    break
            if not title:
                continue

            source = orchestra_url
            if title_link and title_link.get("href"):
                source = urljoin(orchestra_url, title_link.get("href"))
            events.append(make_event(date_str, "杭州", theater, title, source, raw_text=raw))
    except Exception as exc:
        print(f"[warn] zjso official source for {theater}: {exc}")

    return dedupe(events)

def scrape_zhejiang_music_hall() -> list[dict]:
    official = scrape_zhejiang_official_venue("浙江音乐厅")
    if official:
        return official
    print("[warn] 浙江音乐厅 official sources returned zero; using LocalHub fallback")
    return scrape_localhub_venue(
        "浙江音乐厅",
        "https://localhub.to/hangzhou/venue/zhejiang-music-hall/?lang=zh",
    )


def scrape_linping_grand_theater() -> list[dict]:
    return scrape_localhub_venue(
        "临平大剧院",
        "https://localhub.to/hangzhou/venue/hangzhou-linping-theater?lang=zh",
        aliases=("Hangzhou Linping Theater", "杭州临平大剧院"),
    )


def scrape_hangzhou_canal_grand_theater() -> list[dict]:
    official = scrape_zhejiang_official_venue("杭州运河大剧院")
    if official:
        return official
    print("[warn] 杭州运河大剧院 official sources returned zero; keeping previous data via failure")
    raise RuntimeError("official sources returned zero concert events")


def scrape_jinsha_lake_grand_theater() -> list[dict]:
    events: list[dict] = []

    # Official theater social-media feed is used for discovery when server-rendered.
    social_url = "https://www.sina.cn/media/7749068680"
    try:
        soup = BeautifulSoup(fetch(social_url), "html.parser")
        for block in soup.find_all(["article", "li", "p", "div"]):
            text = normalize_title(block.get_text(" ", strip=True))
            if not (20 <= len(text) <= 700):
                continue
            if "金沙湖大剧院" not in text or not is_concert(text):
                continue
            dates = parse_date_strings(text)
            if not dates:
                continue
            title = text
            for node in block.find_all(["a", "h2", "h3", "h4"], limit=6):
                candidate = normalize_title(node.get_text(" ", strip=True))
                if candidate and is_concert(candidate):
                    title = candidate
                    break
            for date_str in dates:
                if valid_future_or_recent(date_str):
                    events.append(make_event(date_str, "杭州", "杭州金沙湖大剧院", title[:240], social_url, raw_text=text))
    except Exception:
        pass

    # A current public ticket listing provides a structured fallback concert entry.
    fallback_url = "https://huodong.com/event/detail/eykzg"
    try:
        soup = BeautifulSoup(fetch(fallback_url), "html.parser")
        text = normalize_title(soup.get_text(" ", strip=True))
        if "金沙湖大剧院" in text and is_concert(text):
            title_node = soup.find("h1")
            title = normalize_title(title_node.get_text(" ", strip=True)) if title_node else "《四月是你的谎言》钢琴小提琴唯美经典音乐会"
            for date_str in parse_date_strings(text):
                if valid_future_or_recent(date_str):
                    events.append(make_event(date_str, "杭州", "杭州金沙湖大剧院", title, fallback_url, raw_text=text))
    except Exception:
        pass

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
    scrapers = [
        ("杭州大剧院", scrape_hangzhou_grand_theater),
        ("杭州剧院", scrape_hangzhou_theater),
        ("浙江音乐厅", scrape_zhejiang_music_hall),
        ("杭州运河大剧院", scrape_hangzhou_canal_grand_theater),
        ("临平大剧院", scrape_linping_grand_theater),
        ("杭州金沙湖大剧院", scrape_jinsha_lake_grand_theater),
    ]

    previous = load_previous()
    previous_events = previous.get("concerts", [])
    fresh_by_theater: dict[str, list[dict]] = {}
    status: list[dict] = []

    for theater, scraper in scrapers:
        try:
            items = dedupe(scraper())
            if not items and theater != "杭州剧院":
                raise RuntimeError("source returned zero concert events")
            fresh_by_theater[theater] = items
            status.append({"source": theater, "ok": True, "count": len(items)})
            print(f"[ok] {theater}: {len(items)} events")
        except Exception as exc:
            status.append({"source": theater, "ok": False, "count": 0, "error": str(exc)[:300]})
            print(f"[error] {theater}: {exc}")

    active_theaters = {name for name, _ in scrapers}
    events: list[dict] = []

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
