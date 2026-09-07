import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B64 = ROOT / "assets" / "apple-touch-icon-piratecat-v3.b64"
ICON = ROOT / "assets" / "apple-touch-icon-piratecat-v3.png"
MANIFEST_ICON = ROOT / "assets" / "icon-180-piratecat-v3.png"
INDEX = ROOT / "index.html"
MANIFEST = ROOT / "manifest.webmanifest"
SW = ROOT / "service-worker.js"

raw = base64.b64decode(B64.read_text(encoding="utf-8").strip())
ICON.write_bytes(raw)
MANIFEST_ICON.write_bytes(raw)

index = INDEX.read_text(encoding="utf-8")
index = index.replace("App v1.3.1", "App v1.3.2")
index = index.replace("apple-touch-icon-piratecat-v2.png", "apple-touch-icon-piratecat-v3.png")
index = index.replace("icon-180-piratecat-v2.png", "icon-180-piratecat-v3.png")
INDEX.write_text(index, encoding="utf-8")

manifest = MANIFEST.read_text(encoding="utf-8")
manifest = manifest.replace("icon-180-piratecat-v2.png", "icon-180-piratecat-v3.png")
MANIFEST.write_text(manifest, encoding="utf-8")

sw = SW.read_text(encoding="utf-8")
sw = sw.replace("concertdate-pwa-app-v1.3.1", "concertdate-pwa-app-v1.3.2")
sw = sw.replace("apple-touch-icon-piratecat-v2.png", "apple-touch-icon-piratecat-v3.png")
sw = sw.replace("icon-180-piratecat-v2.png", "icon-180-piratecat-v3.png")
SW.write_text(sw, encoding="utf-8")

B64.unlink(missing_ok=True)
print(f"Wrote corrected PWA icon ({len(raw)} bytes) and upgraded app to v1.3.2")
