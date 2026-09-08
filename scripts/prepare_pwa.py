import hashlib
import json
import re
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ICON_SOURCE = ROOT / "assets-src" / "pwa-source-ba816ddb.png"


def short_hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:8]


def hashed_copy(source: Path, stem: str, suffix: str) -> str:
    data = source.read_bytes()
    name = f"{stem}-{short_hash_bytes(data)}{suffix}"
    target = ASSETS / name
    if not target.exists():
        target.write_bytes(data)
    return name


def build_icons() -> dict[str, str]:
    image = Image.open(ICON_SOURCE).convert("RGB")
    result = {}
    for key, size, stem in (
        ("apple", 180, "apple-touch-icon"),
        ("192", 192, "icon-192"),
        ("512", 512, "icon-512"),
    ):
        temp = ASSETS / f".{stem}.png"
        image.resize((size, size), Image.Resampling.LANCZOS).save(temp, "PNG", optimize=True)
        data = temp.read_bytes()
        name = f"{stem}-{short_hash_bytes(data)}.png"
        (ASSETS / name).write_bytes(data)
        temp.unlink(missing_ok=True)
        result[key] = name
    return result


def update_index(app_name: str, css_name: str, icons: dict[str, str]) -> None:
    path = ROOT / "index.html"
    html = path.read_text(encoding="utf-8")
    html = re.sub(r'<link rel="stylesheet" href="[^"]+"\s*/?>', f'<link rel="stylesheet" href="./assets/{css_name}" />', html, count=1)
    html = re.sub(r'<script src="[^"]+" defer></script>', f'<script src="./assets/{app_name}" defer></script>', html, count=1)

    html = re.sub(r'\n?\s*<meta name="theme-color"[^>]*>', '', html)
    html = re.sub(r'\n?\s*<meta name="apple-mobile-web-app-[^"]+"[^>]*>', '', html)
    html = re.sub(r'\n?\s*<link rel="manifest"[^>]*>', '', html)
    html = re.sub(r'\n?\s*<link rel="apple-touch-icon"[^>]*>', '', html)
    html = re.sub(r'\n?\s*<link rel="icon"[^>]*>', '', html)

    pwa_head = f'''\n  <meta name="theme-color" content="#111827" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-status-bar-style" content="default" />
  <meta name="apple-mobile-web-app-title" content="ConcertDate" />
  <link rel="manifest" href="./manifest.webmanifest" />
  <link rel="apple-touch-icon" sizes="180x180" href="./assets/{icons['apple']}" />
  <link rel="icon" type="image/png" sizes="192x192" href="./assets/{icons['192']}" />'''
    html = html.replace("  <title>ConcertDate</title>", "  <title>ConcertDate</title>" + pwa_head)

    if "serviceWorker.register" not in html:
        html = html.replace("</body>", """  <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => navigator.serviceWorker.register('./service-worker.js'));
    }
  </script>\n</body>""")
    path.write_text(html, encoding="utf-8")


def write_manifest(icons: dict[str, str]) -> None:
    manifest = {
        "name": "ConcertDate 音乐会日历",
        "short_name": "ConcertDate",
        "description": "按城市、剧院、月份和星期筛选音乐会日期",
        "start_url": "./",
        "scope": "./",
        "display": "standalone",
        "background_color": "#f5f7fb",
        "theme_color": "#111827",
        "icons": [
            {"src": f"./assets/{icons['192']}", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": f"./assets/{icons['512']}", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
    }
    (ROOT / "manifest.webmanifest").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_service_worker(app_name: str, css_name: str, icons: dict[str, str]) -> None:
    static_files = [
        "./", "./index.html", "./manifest.webmanifest",
        f"./assets/{app_name}", f"./assets/{css_name}",
        f"./assets/{icons['apple']}", f"./assets/{icons['192']}", f"./assets/{icons['512']}",
    ]
    version = short_hash_bytes("|".join(static_files).encode())
    worker = f'''const CACHE = 'concertdate-{version}';
const STATIC_FILES = {json.dumps(static_files, ensure_ascii=False)};
self.addEventListener('install', event => {{ event.waitUntil(caches.open(CACHE).then(c => c.addAll(STATIC_FILES))); self.skipWaiting(); }});
self.addEventListener('activate', event => {{ event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))); self.clients.claim(); }});
self.addEventListener('fetch', event => {{
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.pathname.endsWith('/data/concerts.json')) {{
    event.respondWith(fetch(event.request).then(r => {{ const c = r.clone(); caches.open(CACHE).then(cache => cache.put(event.request, c)); return r; }}).catch(() => caches.match(event.request)));
    return;
  }}
  event.respondWith(caches.match(event.request).then(c => c || fetch(event.request)));
}});
'''
    (ROOT / "service-worker.js").write_text(worker, encoding="utf-8")


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    app_source = ROOT / "app.js"
    css_source = ROOT / "styles.css"

    if app_source.exists():
        app_name = hashed_copy(app_source, "app", ".js")
        app_source.unlink()
    else:
        existing = sorted(ASSETS.glob("app-*.js"))
        if not existing:
            raise RuntimeError("hashed app asset not found")
        app_name = existing[-1].name

    if css_source.exists():
        css_name = hashed_copy(css_source, "styles", ".css")
        css_source.unlink()
    else:
        existing = sorted(ASSETS.glob("styles-*.css"))
        if not existing:
            raise RuntimeError("hashed styles asset not found")
        css_name = existing[-1].name

    icons = build_icons()
    update_index(app_name, css_name, icons)
    write_manifest(icons)
    write_service_worker(app_name, css_name, icons)
    print(f"PWA ready: {app_name}, {css_name}, {icons}")


if __name__ == "__main__":
    main()
