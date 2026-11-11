"""Register the upstream numeric benchmark name against our fixed local artifact."""
import hashlib
import json
from pathlib import Path
from lits.benchmarks.registry import register_dataset
# Import the author's numeric correctness checker, without importing the unpinned loader.
from demos.lits_benchmark.math_qa_eval import evaluate_math_qa  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "assignment/data/math500_numeric.jsonl"


@register_dataset("math500", task_type="language_grounded")
def load_math500(**kwargs):
    if kwargs:
        raise ValueError(f"Dataset overrides are unsupported: {sorted(kwargs)}")
    manifest = json.loads((DATA.parent / "manifest.json").read_text(encoding="utf-8"))
    if hashlib.sha256(DATA.read_bytes()).hexdigest() != manifest["sha256"]:
        raise ValueError("Dataset integrity check failed")
    rows = [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != manifest["total_rows"]:
        raise ValueError("Dataset row count differs from manifest")
    return rows
