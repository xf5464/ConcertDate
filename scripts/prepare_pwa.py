import base64
import hashlib
import json
import re
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ICON_SOURCE = ROOT / "assets-src" / "apple-touch-icon.b64"


def short_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:8]


def hashed_copy(source: Path, stem: str, suffix: str) -> str:
    digest = short_hash(source)
    target_name = f"{stem}-{digest}{suffix}"
    target = ASSETS / target_name
    shutil.copy2(source, target)
    return target_name


def build_icons() -> dict[str, str]:
    if not ICON_SOURCE.exists():
        existing = {
            "apple": next(ASSETS.glob("apple-touch-icon-*.png"), None),
            "192": next(ASSETS.glob("icon-192-*.png"), None),
            "512": next(ASSETS.glob("icon-512-*.png"), None),
        }
        if all(existing.values()):
            return {k: v.name for k, v in existing.items()}
        raise RuntimeError("PWA icon source is missing and generated icons were not found")

    raw = base64.b64decode(ICON_SOURCE.read_text(encoding="utf-8").strip())
    temp = ASSETS / ".icon-source.png"
    temp.write_bytes(raw)

    image = Image.open(temp).convert("RGB")
    result: dict[str, str] = {}
    for key, size, stem in (
        ("apple", 180, "apple-touch-icon"),
        ("192", 192, "icon-192"),
        ("512", 512, "icon-512"),
    ):
        out = ASSETS / f".{stem}.png"
        resized = image.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(out, "PNG", optimize=True)
        digest = short_hash(out)
        final = ASSETS / f"{stem}-{digest}.png"
        out.replace(final)
        result[key] = final.name

    temp.unlink(missing_ok=True)
    ICON_SOURCE.unlink(missing_ok=True)
    try:
        ICON_SOURCE.parent.rmdir()
    except OSError:
        pass
    return result


def update_index(app_name: str, css_name: str, icons: dict[str, str]) -> None:
    path = ROOT / "index.html"
    html = path.read_text(encoding="utf-8")

    html = re.sub(
        r'<link rel="stylesheet" href="[^"]+"\s*/?>',
        f'<link rel="stylesheet" href="./assets/{css_name}" />',
        html,
        count=1,
    )
    html = re.sub(
        r'<script src="[^"]+" defer></script>',
        f'<script src="./assets/{app_name}" defer></script>',
        html,
        count=1,
    )

    pwa_head = f'''\n  <meta name="theme-color" content="#111827" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-status-bar-style" content="default" />
  <meta name="apple-mobile-web-app-title" content="ConcertDate" />
  <link rel="manifest" href="./manifest.webmanifest" />
  <link rel="apple-touch-icon" sizes="180x180" href="./assets/{icons['apple']}" />
  <link rel="icon" type="image/png" sizes="192x192" href="./assets/{icons['192']}" />'''

    if 'rel="manifest"' not in html:
        html = html.replace("  <title>ConcertDate</title>", "  <title>ConcertDate</title>" + pwa_head)

    registration = '''\n  <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => navigator.serviceWorker.register('./service-worker.js'));
    }
  </script>'''
    if "serviceWorker.register" not in html:
        html = html.replace("</body>", registration + "\n</body>")

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
            {
                "src": f"./assets/{icons['192']}",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable",
            },
            {
                "src": f"./assets/{icons['512']}",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable",
            },
        ],
    }
    (ROOT / "manifest.webmanifest").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def write_service_worker(app_name: str, css_name: str, icons: dict[str, str]) -> None:
    cache_files = [
        "./",
        "./index.html",
        "./manifest.webmanifest",
        f"./assets/{app_name}",
        f"./assets/{css_name}",
        f"./assets/{icons['apple']}",
        f"./assets/{icons['192']}",
        f"./assets/{icons['512']}",
    ]
    cache_json = json.dumps(cache_files, ensure_ascii=False)
    worker = f'''const CACHE = 'concertdate-v1';
const STATIC_FILES = {cache_json};

self.addEventListener('install', event => {{
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(STATIC_FILES)));
  self.skipWaiting();
}});

self.addEventListener('activate', event => {{
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key))))
  );
  self.clients.claim();
}});

self.addEventListener('fetch', event => {{
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET') return;

  if (url.pathname.endsWith('/data/concerts.json')) {{
    event.respondWith(
      fetch(event.request)
        .then(response => {{
          const copy = response.clone();
          caches.open(CACHE).then(cache => cache.put(event.request, copy));
          return response;
        }})
        .catch(() => caches.match(event.request))
    );
    return;
  }}

  event.respondWith(
    caches.match(event.request).then(cached => cached || fetch(event.request))
  );
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
        existing = next(ASSETS.glob("app-*.js"), None)
        if not existing:
            raise RuntimeError("app.js or hashed app asset not found")
        app_name = existing.name

    if css_source.exists():
        css_name = hashed_copy(css_source, "styles", ".css")
        css_source.unlink()
    else:
        existing = next(ASSETS.glob("styles-*.css"), None)
        if not existing:
            raise RuntimeError("styles.css or hashed styles asset not found")
        css_name = existing.name

    icons = build_icons()
    update_index(app_name, css_name, icons)
    write_manifest(icons)
    write_service_worker(app_name, css_name, icons)

    print(f"PWA assets ready: {app_name}, {css_name}, {icons}")


if __name__ == "__main__":
    main()
