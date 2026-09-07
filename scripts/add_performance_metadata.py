from pathlib import Path

path = Path(__file__).resolve().parent / "scrape.py"
text = path.read_text(encoding="utf-8")

if "def parse_start_time(" not in text:
    anchor = '''def normalize_title(text: str) -> str:\n    return re.sub(r"\\s+", " ", text).strip(" -｜|·\\n\\t")\n\n\n'''
    addition = '''def normalize_title(text: str) -> str:\n    return re.sub(r"\\s+", " ", text).strip(" -｜|·\\n\\t")\n\n\ndef parse_start_time(text: str) -> str | None:\n    value = normalize_title(text)\n    # Prefer explicit HH:MM. Avoid treating years/dates as times.\n    match = re.search(r"(?<!\\d)([01]?\\d|2[0-3])[:：]([0-5]\\d)(?!\\d)", value)\n    if not match:\n        return None\n    return f"{int(match.group(1)):02d}:{match.group(2)}"\n\n\ndef parse_duration(text: str) -> tuple[int | None, str | None]:\n    value = normalize_title(text)\n    # Only keep duration when the source explicitly states it. Never infer.\n    patterns = [\n        r"(?:演出时长|演出时间|时长|全长|约)[:：\\s]*约?\\s*(\\d{2,3})\\s*分钟",\n        r"约\\s*(\\d{2,3})\\s*分钟",\n        r"(\\d{2,3})\\s*分钟(?:左右|约)?",\n    ]\n    for pattern in patterns:\n        match = re.search(pattern, value)\n        if match:\n            minutes = int(match.group(1))\n            if 20 <= minutes <= 360:\n                return minutes, f"约{minutes}分钟" if "约" in match.group(0) else f"{minutes}分钟"\n    return None, None\n\n\n'''
    if anchor not in text:
        raise SystemExit("normalize_title anchor not found")
    text = text.replace(anchor, addition, 1)

old_make = '''def make_event(date_str: str, city: str, theater: str, title: str, source: str):\n    return {\n        "date": date_str,\n        "city": city,\n        "theater": theater,\n        "title": normalize_title(title),\n        "source": source,\n    }\n'''
new_make = '''def make_event(date_str: str, city: str, theater: str, title: str, source: str, raw_text: str = "", start_time: str | None = None):\n    event = {\n        "date": date_str,\n        "city": city,\n        "theater": theater,\n        "title": normalize_title(title),\n        "source": source,\n    }\n    source_text = raw_text or title\n    parsed_time = start_time or parse_start_time(source_text)\n    if parsed_time:\n        event["startTime"] = parsed_time\n    duration_minutes, duration_text = parse_duration(source_text)\n    if duration_minutes is not None:\n        event["durationMinutes"] = duration_minutes\n    if duration_text:\n        event["durationText"] = duration_text\n    return event\n'''
if old_make in text:
    text = text.replace(old_make, new_make, 1)
elif new_make not in text:
    raise SystemExit("make_event block not found")

# LocalHub and card scrapers already have the full card text in `text` or `raw`.
text = text.replace('make_event(date_str, "杭州", theater, title, url)', 'make_event(date_str, "杭州", theater, title, url, raw_text=text)')
text = text.replace('make_event(date_str, "杭州", theater, title, source)', 'make_event(date_str, "杭州", theater, title, source, raw_text=raw)')
text = text.replace('make_event(date_str, "杭州", "杭州金沙湖大剧院", title[:240], social_url)', 'make_event(date_str, "杭州", "杭州金沙湖大剧院", title[:240], social_url, raw_text=text)')
text = text.replace('make_event(date_str, "杭州", "杭州金沙湖大剧院", title, fallback_url)', 'make_event(date_str, "杭州", "杭州金沙湖大剧院", title, fallback_url, raw_text=text)')

# ZJSO exposes date/time in the HTML datetime attribute; preserve clock time when present.
old_zjso = 'events.append(make_event(date_str, "杭州", theater, title, source))'
new_zjso = '''\n            explicit_time = None\n            time_match = re.search(r"[T\\s](\\d{2}):(\\d{2})", raw_dt)\n            if time_match:\n                explicit_time = f"{time_match.group(1)}:{time_match.group(2)}"\n            events.append(make_event(date_str, "杭州", theater, title, source, raw_text=context_text, start_time=explicit_time))'''
if old_zjso in text:
    text = text.replace(old_zjso, new_zjso, 1)

path.write_text(text, encoding="utf-8")
print("Performance metadata extraction enabled: startTime + explicit duration only")
