from pathlib import Path
import base64
import re
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
    img.resize((size, size), Image.Resampling.LANCZOS).save(
        ASSETS / name,
        format="PNG",
        optimize=True,
    )

index = INDEX.read_text(encoding="utf-8")
index = index.replace("apple-touch-icon-piratecat-v2.png", "apple-touch-icon-piratecat-v4.png")
index = index.replace("icon-180-piratecat-v2.png", "icon-192-piratecat-v4.png")
index = index.replace('sizes="180x180" href="./assets/icon-192-piratecat-v4.png"', 'sizes="192x192" href="./assets/icon-192-piratecat-v4.png"')
index = index.replace("App v1.3.1", "App v1.3.2")
INDEX.write_text(index, encoding="utf-8")

MANIFEST.write_text(
    '''{
  "name": "ConcertDate 音乐会日历",
  "short_name": "ConcertDate",
  "description": "按城市、剧院、月份和星期筛选音乐会日期",
  "start_url": "./",
  "scope": "./",
  "display": "standalone",
  "background_color": "#f5f7fb",
  "theme_color": "#111827",
  "icons": [
    {
      "src": "./assets/icon-192-piratecat-v4.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "./assets/icon-512-piratecat-v4.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ]
}
''',
    encoding="utf-8",
)

sw = SW.read_text(encoding="utf-8")
sw = re.sub(
    r"const CACHE = 'concertdate-pwa-app-v[^']+';",
    "const CACHE = 'concertdate-pwa-app-v1.3.2';",
    sw,
)

old_icon_lines = [
    "  './assets/apple-touch-icon-piratecat-v1.png',\n",
    "  './assets/apple-touch-icon-piratecat-v2.png',\n",
    "  './assets/icon-180-piratecat-v1.png',\n",
    "  './assets/icon-180-piratecat-v2.png',\n",
]
for old in old_icon_lines:
    sw = sw.replace(old, "")

new_icon_lines = (
    "  './assets/apple-touch-icon-piratecat-v4.png',\n"
    "  './assets/icon-192-piratecat-v4.png',\n"
    "  './assets/icon-512-piratecat-v4.png',\n"
)
if "apple-touch-icon-piratecat-v4.png" not in sw:
    sw = sw.replace("];\n", new_icon_lines + "];\n", 1)
SW.write_text(sw, encoding="utf-8")

SRC.unlink()
print("Built valid PWA icons and updated app to v1.3.2")
