from pathlib import Path

path = Path(__file__).resolve().parent / "scrape.py"
text = path.read_text(encoding="utf-8")

old_infer = '''def infer_year(month: int) -> int:\n    today = date.today()\n    if month < today.month - 4:\n        return today.year + 1\n    return today.year\n'''
new_infer = '''def infer_year(text: str, month: int, day_num: int) -> int:\n    \"\"\"Infer a missing year conservatively from the displayed weekday.\n\n    LocalHub often renders dates as e.g. `3/21 周六` without a year.  The old\n    month-only heuristic incorrectly turned past 2026 performances into 2027\n    performances.  Prefer the calendar year whose weekday matches the source;\n    without a weekday, keep the current year so stale past listings are filtered\n    out instead of being invented as future events.\n    \"\"\"\n    today = date.today()\n    weekday_match = re.search(r\"周([一二三四五六日天])\", text)\n    weekday_map = {\"一\": 0, \"二\": 1, \"三\": 2, \"四\": 3, \"五\": 4, \"六\": 5, \"日\": 6, \"天\": 6}\n\n    if weekday_match:\n        expected = weekday_map[weekday_match.group(1)]\n        for year in (today.year, today.year + 1, today.year - 1):\n            try:\n                candidate = date(year, month, day_num)\n            except ValueError:\n                continue\n            if candidate.weekday() == expected:\n                return year\n\n    return today.year\n'''

old_call = '''        month, day_num = int(match.group(1)), int(match.group(2))\n        try:\n            return [date(infer_year(month), month, day_num).isoformat()]\n        except ValueError:\n            return []\n'''
new_call = '''        month, day_num = int(match.group(1)), int(match.group(2))\n        try:\n            return [date(infer_year(text, month, day_num), month, day_num).isoformat()]\n        except ValueError:\n            return []\n'''

if old_infer in text:
    text = text.replace(old_infer, new_infer, 1)
elif new_infer not in text:
    raise SystemExit("Could not locate infer_year block")

if old_call in text:
    text = text.replace(old_call, new_call, 1)
elif new_call not in text:
    raise SystemExit("Could not locate infer_year call")

path.write_text(text, encoding="utf-8")
print("Performance-date year inference fixed: source weekday now decides missing year")
