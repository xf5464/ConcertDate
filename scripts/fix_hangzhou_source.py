from pathlib import Path

path = Path(__file__).resolve().parent / "scrape.py"
text = path.read_text(encoding="utf-8")
old = 'url = "https://zjyy99.com/listZxdp/24.html"'
new = 'url = "https://www.zjyy99.com/"'
if old in text:
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    print("Updated Hangzhou Theatre source to the official www.zjyy99.com host")
else:
    print("Hangzhou Theatre source was already updated")
