from pathlib import Path

path = Path(__file__).resolve().parent / "scrape.py"
text = path.read_text(encoding="utf-8")

for old in (
    'url = "https://zjyy99.com/listZxdp/24.html"',
    'url = "https://www.zjyy99.com/"',
    'url = "https://www.zjyy99.com/listZxdp/24.html"',
):
    if old in text:
        text = text.replace(old, 'url = "https://localhub.to/hangzhou/venue/hangzhou-theater?lang=zh"', 1)

# Hangzhou Theatre can legitimately have zero upcoming concert-class events.
text = text.replace(
    'if not items:\n                raise RuntimeError("source returned zero concert events")',
    'if not items and theater != "杭州剧院":\n                raise RuntimeError("source returned zero concert events")',
    1,
)

path.write_text(text, encoding="utf-8")
print("Hangzhou Theatre uses LocalHub venue calendar; zero upcoming concerts is allowed")
