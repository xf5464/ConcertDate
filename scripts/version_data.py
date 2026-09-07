import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "concerts.json"
VERSION_FILE = ROOT / "data" / "version.json"


def main() -> None:
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    stable_payload = {
        "cities": payload.get("cities", []),
        "concerts": payload.get("concerts", []),
    }
    raw = json.dumps(
        stable_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    version = hashlib.sha256(raw).hexdigest()[:12]

    versioned_payload = {"version": version}
    versioned_payload.update({key: value for key, value in payload.items() if key != "version"})

    DATA_FILE.write_text(
        json.dumps(versioned_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    VERSION_FILE.write_text(
        json.dumps({"version": version}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Concert data version: {version}")


if __name__ == "__main__":
    main()
