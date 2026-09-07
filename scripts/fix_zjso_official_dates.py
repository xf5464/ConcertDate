from pathlib import Path

path = Path(__file__).resolve().parent / "scrape.py"
text = path.read_text(encoding="utf-8")
old = '''            raw_dt = str(time_node.get("datetime") or "")
            m = re.search(r"(20\\\\d{2}-\\\\d{2}-\\\\d{2})", raw_dt)
            if not m:
                continue
            date_str = m.group(1)
'''
new = '''            raw_dt = str(time_node.get("datetime") or "")
            date_str = raw_dt[:10]
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                continue
'''
if old in text:
    text = text.replace(old, new, 1)
elif 'm = re.search(r"(20\\\\d{2}-\\\\d{2}-\\\\d{2})", raw_dt)' in text:
    text = text.replace(
        '            m = re.search(r"(20\\\\d{2}-\\\\d{2}-\\\\d{2})", raw_dt)\n            if not m:\n                continue\n            date_str = m.group(1)\n',
        '            date_str = raw_dt[:10]\n            try:\n                datetime.strptime(date_str, "%Y-%m-%d")\n            except ValueError:\n                continue\n',
        1,
    )
else:
    print("ZJSO datetime parser already fixed or pattern changed")

path.write_text(text, encoding="utf-8")
print("ZJSO official calendar now reads the explicit HTML datetime directly")
