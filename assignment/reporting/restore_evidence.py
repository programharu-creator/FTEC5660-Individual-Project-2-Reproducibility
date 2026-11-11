"""Restore committed experiment evidence locally, without model calls or API keys."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    evidence = ROOT / "assignment/evidence"
    index = json.loads((evidence / "index.json").read_text(encoding="utf-8"))
    for item in index["formal_runs"]:
        source = evidence / item["evidence_directory"]
        target = ROOT / "assignment/runs" / item["run_directory"]
        if target.exists():
            print("EXISTS", target.name)
            continue
        target.mkdir(parents=True)
        for filename in ["run_manifest.json", "usage_summary.json", "eval_results.json", "config.json",
                         "api_calls.jsonl", "eval.log"]:
            (target / filename).write_bytes((source / filename).read_bytes())
        (target / "source_hashes.json").write_bytes((evidence / "common_source_hashes.json").read_bytes())
        for bundle, subdirectory in [("full_trees.jsonl", "full_tree"), ("terminal_nodes.jsonl", "terminal_nodes"),
                                     ("search_facts.jsonl", "")]:
            for line in (source / bundle).read_text(encoding="utf-8").splitlines():
                record = json.loads(line)
                name = record["filename"]
                if Path(name).name != name or not name.endswith(".json"):
                    raise ValueError("Unexpected evidence filename")
                path = target / subdirectory / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(record["content"], ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        print("RESTORED", target.name)


if __name__ == "__main__":
    main()
