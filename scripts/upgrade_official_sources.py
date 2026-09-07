from pathlib import Path
import re

path = Path(__file__).resolve().parent / "scrape.py"
text = path.read_text(encoding="utf-8")

if "from urllib.parse import urljoin" not in text:
    text = text.replace("from typing import Iterable\n", "from typing import Iterable\nfrom urllib.parse import urljoin\n", 1)

helper = r'''

def scrape_zhejiang_official_venue(theater: str) -> list[dict]:
    """Official-source-first scraper for Zhejiang Music Hall / Hangzhou Canal Grand Theatre.

    Priority:
    1) Zhejiang Performing Arts Group official ticket page (broad venue coverage)
    2) Zhejiang Symphony Orchestra official calendar (orchestral concerts)
    The caller may fall back to LocalHub only when both official sources return zero.
    """
    events: list[dict] = []

    # Official ticket platform operated by Zhejiang Performing Arts Group.
    ticket_url = "https://www.zjyy99.com/listZxdp/24.html"
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
                    events.append(make_event(date_str, "杭州", theater, title, source))
    except Exception as exc:
        print(f"[warn] zjyy99 official source for {theater}: {exc}")

    # Zhejiang Symphony Orchestra official event calendar. This is especially
    # useful for concerts at Hangzhou Canal Grand Theatre and Zhejiang Music Hall.
    orchestra_url = "https://www.zjso.org/yugao/"
    try:
        soup = BeautifulSoup(fetch(orchestra_url), "html.parser")
        for time_node in soup.find_all("time", attrs={"datetime": True}):
            raw_dt = str(time_node.get("datetime") or "")
            m = re.search(r"(20\\d{2}-\\d{2}-\\d{2})", raw_dt)
            if not m:
                continue
            date_str = m.group(1)
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
            events.append(make_event(date_str, "杭州", theater, title, source))
    except Exception as exc:
        print(f"[warn] zjso official source for {theater}: {exc}")

    return dedupe(events)
'''

if "def scrape_zhejiang_official_venue(" not in text:
    marker = "\ndef scrape_zhejiang_music_hall() -> list[dict]:\n"
    if marker not in text:
        raise SystemExit("Could not locate Zhejiang Music Hall scraper insertion point")
    text = text.replace(marker, helper + marker, 1)

music_pattern = re.compile(
    r"def scrape_zhejiang_music_hall\(\) -> list\[dict\]:\n.*?(?=\ndef scrape_linping_grand_theater\(\) -> list\[dict\]:)",
    re.S,
)
music_replacement = '''def scrape_zhejiang_music_hall() -> list[dict]:
    official = scrape_zhejiang_official_venue("浙江音乐厅")
    if official:
        return official
    print("[warn] 浙江音乐厅 official sources returned zero; using LocalHub fallback")
    return scrape_localhub_venue(
        "浙江音乐厅",
        "https://localhub.to/hangzhou/venue/zhejiang-music-hall/?lang=zh",
    )

'''
text, count = music_pattern.subn(music_replacement, text, count=1)
if count != 1:
    raise SystemExit("Could not replace Zhejiang Music Hall scraper")

canal_pattern = re.compile(
    r"def scrape_hangzhou_canal_grand_theater\(\) -> list\[dict\]:\n.*?(?=\ndef scrape_jinsha_lake_grand_theater\(\) -> list\[dict\]:)",
    re.S,
)
canal_replacement = '''def scrape_hangzhou_canal_grand_theater() -> list[dict]:
    official = scrape_zhejiang_official_venue("杭州运河大剧院")
    if official:
        return official
    print("[warn] 杭州运河大剧院 official sources returned zero; keeping previous data via failure")
    raise RuntimeError("official sources returned zero concert events")

'''
text, count = canal_pattern.subn(canal_replacement, text, count=1)
if count != 1:
    raise SystemExit("Could not replace Hangzhou Canal Grand Theatre scraper")

path.write_text(text, encoding="utf-8")
print("Official-source priority enabled for 浙江音乐厅 and 杭州运河大剧院")
