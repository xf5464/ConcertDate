from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = ROOT / "assets-src"
head = src / "apple-touch-icon.b64"
parts = sorted(src.glob("icon-*.b64"))

if not head.exists():
    print("Icon source already assembled or generated; nothing to do")
elif parts:
    combined = head.read_text(encoding="utf-8").strip()
    for part in parts:
        combined += part.read_text(encoding="utf-8").strip()
    head.write_text(combined, encoding="utf-8")
    for part in parts:
        part.unlink()
    print(f"Assembled PWA icon from {1 + len(parts)} chunks ({len(combined)} base64 chars)")
else:
    print("PWA icon source is already a single file")
