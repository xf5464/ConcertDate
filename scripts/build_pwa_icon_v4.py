from pathlib import Path
import base64
from io import BytesIO
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets-src" / "piratecat-v4.jpg.b64"
ASSETS = ROOT / "assets"
INDEX = ROOT / "index.html"
MANIFEST = ROOT / "manifest.webmanifest"
SW = ROOT / "service-worker.js"

raw = base64.b64decode(SRC.read_text(encoding="utf-8").strip(), validate=True)
img = Image.open(BytesIO(raw)).convert("RGB")

for size, name in [
    (180, "apple-touch-icon-piratecat-v4.png"),
    (192, "icon-192-piratecat-v4.png"),
    (512, "icon-512-piratecat-v4.png"),
]:
    out = img.resize((size, size), Image.Resampling.LANCZOS)
    out.save(ASSETS / name, format="PNG", optimize=True)

index = INDEX.read_text(encoding="utf-8")
index = index.replace("apple-touch-icon-piratecat-v2.png", "apple-touch-icon-piratecat-v4.png")
index = index.replace("icon-180-piratecat-v2.png", "icon-192-piratecat-v4.png")
index = index.replace('sizes="180x180" href="./assets/icon-192-piratecat-v4.png"', 'sizes="192x192" href="./assets/icon-192-piratecat-v4.png"')
index = index.replace("App v1.3.1", "App v1.3.2")
INDEX.write_text(index, encoding="utf-8")

MANIFEST.write_text('''{\n  "name": "ConcertDate 音乐会日历",\n  "short_name": "ConcertDate",\n  "description": "按城市、剧院、月份和星期筛选音乐会日期",\n  "start_url": "./",\n  "scope": "./",\n  "display": "standalone",\n  "background_color": "#f5f7fb",\n  "theme_color": "#111827",\n  "icons": [\n    {\n      "src": "./assets/icon-192-piratecat-v4.png",\n      "sizes": "192x192",\n      "type": "image/png",\n      "purpose": "any"\n    },\n    {\n      "src": "./assets/icon-512-piratecat-v4.png",\n      "sizes": "512x512",\n      "type": "image/png",\n      "purpose": "any maskable"\n    }\n  ]\n}\n''', encoding="utf-8")

sw = SW.read_text(encoding="utf-8")
import re
sw = re.sub(r"const CACHE = 'concertdate-pwa-app-v[^']+';", "const CACHE = 'concertdate-pwa-app-v1.3.2';", sw)
for old in [
    "./assets/apple-touch-icon-piratecat-v1.png",
    "./assets/apple-touch-icon-piratecat-v2.png",
    "./assets/icon-180-piratecat-v1.png",
    "./assets/icon-180-piratecat-v2.png",
]:
    sw = sw.replace(f"  '{old}',\n", "")
insert = "  './assets/apple-touch-icon-piratecat-v4.png',\n  './assets/icon-192-piratecat-v4.png',\n  './assets/icon-512-piratecat-v4.png',\n"
needle = "];
"
if "apple-touch-icon-piratecat-v4.png" not in sw:
    sw = sw.replace(needle, insert + needle, 1)
SW.write_text(sw, encoding="utf-8")

SRC.unlink()
print("Built valid PWA icons and updated app to v1.3.2")
