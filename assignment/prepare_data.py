"""Download a fixed public dataset artifact; no model key or inference calls."""
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = json.loads((ROOT / "assignment/experiment_plan.json").read_text(encoding="utf-8"))
DATA = ROOT / "assignment/data/math500_numeric.jsonl"
MANIFEST = ROOT / "assignment/data/manifest.json"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    spec = PLAN["dataset"]
    url = f"https://huggingface.co/datasets/{spec['repo']}/resolve/{spec['revision']}/{spec['filename']}"
    DATA.parent.mkdir(parents=True, exist_ok=True)
    if not DATA.exists():
        with urllib.request.urlopen(url, timeout=60) as response:
            content = response.read()
        # Validate before persisting a successful artifact.
        rows = [json.loads(line) for line in content.decode("utf-8").splitlines() if line.strip()]
        if len(rows) < spec["formal_count"] or any("question" not in row or "answer" not in row for row in rows):
            raise ValueError("Unexpected dataset schema or insufficient rows")
        DATA.write_bytes(content)
    rows = [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line.strip()]
    digest = sha256(DATA)
    if MANIFEST.exists():
        previous = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if previous["sha256"] != digest:
            raise ValueError("Local data differs from its recorded SHA256")
        print(f"DATA_VERIFIED rows={len(rows)} sha256={digest}")
        return
    manifest = {**spec, "source_url": url, "sha256": digest, "total_rows": len(rows),
                "formal_indices": list(range(spec["formal_count"])),
                "pilot_indices": list(range(spec["pilot_count"])),
                "downloaded_at_utc": datetime.now(timezone.utc).isoformat()}
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"DATA_PREPARED rows={len(rows)} sha256={digest}")


if __name__ == "__main__":
    main()
