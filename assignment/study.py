"""Controlled LiTS experiment launcher. No API calls occur in plan/preflight."""
import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "assignment/experiment_plan.json"
PLAN = json.loads(PLAN_PATH.read_text(encoding="utf-8"))


def stamp():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parameters(phase, max_steps=None, seed=11, call_limit=None):
    p = dict(PLAN["study"])
    p.update(phase=phase, seed=seed, count=PLAN["dataset"]["formal_count"])
    if phase != "formal":
        p.update(PLAN[phase])
    p["max_steps"] = max_steps if max_steps is not None else p.get("max_steps", 10)
    if isinstance(p["max_steps"], list):
        p["max_steps"] = PLAN["study"]["baseline_max_steps"]
    p["call_limit"] = call_limit if call_limit is not None else p.get("call_limit", p["count"] * 500)
    if p["max_steps"] <= 0 or p["call_limit"] <= 0:
        raise ValueError("Step and call limits must be positive")
    if phase == "formal" and p["max_steps"] not in PLAN["study"]["max_steps"]:
        raise ValueError("Formal depth must match the registered experiment plan")
    return p


def search_args(p, output, model, dry_run=False):
    args = [
        "lits-search", "--include", "assignment.benchmark", "--dataset", "math500",
        "--search_framework", "rest", "--policy", "concat", "--transition", "concat",
        "--reward", "generative", "--policy-model", f"openai/{model}",
        "--eval-model", f"openai/{model}", "--cfg", "search_algorithm=mcts",
        "--search-arg",
        f"max_steps={p['max_steps']}", f"n_iters={p['n_iters']}",
        f"n_actions={p['n_actions']}", f"roll_out_steps={p['roll_out_steps']}",
        "n_action_for_simulate=1", "n_confidence=1",
        "force_terminating_on_depth_limit=True", "terminate_on_first_solution=True",
        f"sample_size_terminate={p['sample_size_terminate']}",
        "enable_think_policy=False", "enable_think_eval=False",
        "enable_think_terminal_gen=False", "add_continuation=False",
        "--component-arg", f"max_new_tokens={p['policy_max_new_tokens']}",
        f"n_for_correctness={p['n_for_correctness']}",
        f"n_for_usefulness={p['n_for_usefulness']}",
        "think_for_correctness=False", "think_for_usefulness=False",
        "--var", "offset=0", f"limit={p['count']}", "-o", str(output),
    ]
    if dry_run:
        args.append("--dry-run")
    return args


def invoke(main, args):
    previous = sys.argv
    sys.argv = args
    try:
        code = main()
        if code not in (None, 0):
            raise RuntimeError(f"Command returned {code}")
    finally:
        sys.argv = previous


class CallLimitReached(SystemExit):
    """Abort without being caught by per-component fallback/retry handlers."""


class APIRequestFailed(SystemExit):
    """Do not turn provider failures into model correctness failures."""


class Ledger:
    def __init__(self, path, limit):
        self.path, self.limit, self.count, self.phase = Path(path), limit, 0, "search"

    def wrap(self, request):
        def call(fn, *args, **kwargs):
            if self.count >= self.limit:
                raise CallLimitReached("Configured model-call cap reached; run remains incomplete")
            self.count += 1
            begin = time.perf_counter()
            rec = {
                "call": self.count, "phase": self.phase, "at_utc": stamp(),
                "request": {k: kwargs.get(k) for k in
                            ("model", "temperature", "top_p", "max_tokens", "n", "stop", "extra_body")},
                "prompt_sha256": hashlib.sha256(json.dumps(kwargs.get("messages", []),
                    ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest(),
            }
            try:
                response = request(fn, *args, **kwargs)
                rec.update(status="ok", response_id=response.id, served_model=response.model,
                           usage=response.usage.model_dump(mode="json") if response.usage else {},
                           finish_reasons=[x.finish_reason for x in response.choices])
                return response
            except Exception as exc:
                rec.update(status="error", error_type=type(exc).__name__)
                raise APIRequestFailed("Model API request failed: " + type(exc).__name__) from None
            except BaseException as exc:
                rec.update(status="error", error_type=type(exc).__name__)
                raise
            finally:
                rec["seconds"] = time.perf_counter() - begin
                with self.path.open("a", encoding="utf-8") as file:
                    file.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return call


def source_fingerprint():
    files = list((ROOT / "lits").rglob("*.py")) + list((ROOT / "assignment").glob("*.py"))
    files += [PLAN_PATH, ROOT / "assignment/requirements-api.lock.txt"]
    return {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(files)}


def read_calls(output):
    path = Path(output) / "api_calls.jsonl"
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def summarize(output):
    output = Path(output)
    records = read_calls(output)
    metrics = {}
    for phase in ("search", "evaluation"):
        selected = [x for x in records if x["phase"] == phase]
        metrics[phase] = {
            "calls": len(selected),
            "successful_calls": sum(x["status"] == "ok" for x in selected),
            "input_tokens": sum(x.get("usage", {}).get("prompt_tokens", 0) for x in selected),
            "output_tokens": sum(x.get("usage", {}).get("completion_tokens", 0) for x in selected),
            "api_wall_seconds": sum(x["seconds"] for x in selected),
        }
    metrics["served_models"] = sorted({x["served_model"] for x in records if x.get("served_model")})
    eval_path = output / "eval_results.json"
    metrics["evaluation"] = {**metrics["evaluation"],
                             "upstream_results": json.loads(eval_path.read_text(encoding="utf-8")) if eval_path.exists() else None}
    # Node dictionaries omit depth; reconstruct it from full-tree child links.
    per_question = []
    for path in sorted((output / "full_tree").glob("full_tree_*.json")):
        tree = json.loads(path.read_text(encoding="utf-8"))
        frontier, observed = [(tree, 0)], 0
        while frontier:
            node, depth = frontier.pop()
            observed = max(observed, depth)
            frontier.extend((child, depth + 1) for child in node.get("children", []))
        per_question.append({"query_idx": int(path.stem.rsplit("_", 1)[1]), "max_depth": observed})
    metrics["per_question_depth"] = per_question
    metrics["max_observed_depth"] = max((x["max_depth"] for x in per_question), default=None)
    metrics["mean_max_observed_depth"] = (
        sum(x["max_depth"] for x in per_question) / len(per_question) if per_question else None)
    write_json(output / "usage_summary.json", metrics)
    return metrics


def preflight():
    from assignment.benchmark import load_math500
    from demos.lits_benchmark.math_qa_eval import evaluate_math_qa
    from lits.config import ExperimentConfig
    from lits.cli.search import main as search_main
    from lits.lm.openai_chat import OpenAIChatModel  # noqa: F401
    from dotenv import dotenv_values
    rows = load_math500()
    assert evaluate_math_qa("42", "42")
    assert evaluate_math_qa("42", "41") is False
    assert evaluate_math_qa("2.0", "2")
    p = parameters("smoke")
    # Test the resolved real MCTS configuration, not just our JSON plan.
    resolved = ExperimentConfig(dataset="math500", policy_model_name="openai/deepseek-flash",
        eval_model_name="openai/deepseek-flash", search_framework="rest",
        search_args={"max_steps": 3, "n_iters": 1, "force_terminating_on_depth_limit": True})
    config = resolved.create_search_config()
    assert config.max_steps == 3 and config.force_terminating_on_depth_limit is True
    invoke(search_main, search_args(p, ROOT / "assignment/runs/PREFLIGHT_NOT_CREATED",
                                   PLAN["model"]["name"], dry_run=True))
    values = dotenv_values(ROOT / ".env")
    key_present = bool(os.getenv("DEEPSEEK_API_KEY") or values.get("DEEPSEEK_API_KEY"))
    result = {"status": "passed", "python": platform.python_version(), "dataset_rows": len(rows),
              "formal_rows": PLAN["dataset"]["formal_count"], "depth_cap_enabled": True,
              "numeric_checker": "passed", "api_key": "present" if key_present else "missing",
              "real_api_calls": 0}
    print(json.dumps(result, indent=2))


def run(p):
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", override=False)
    key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not key:
        raise SystemExit("API key missing. Fill DEEPSEEK_API_KEY in the project-root .env first.")
    model = os.getenv("DEEPSEEK_MODEL") or PLAN["model"]["name"]
    endpoint = os.getenv("DEEPSEEK_BASE_URL") or PLAN["model"]["base_url"]
    from urllib.parse import urlparse
    if urlparse(endpoint).hostname != "api.deepseek.com" or urlparse(endpoint).scheme != "https":
        raise SystemExit("This study uses the official HTTPS DeepSeek endpoint; update the plan for another provider.")
    os.environ["OPENAI_API_KEY"] = key
    os.environ["OPENAI_API_BASE"] = endpoint
    os.environ["LITS_NETWORK_RECOVERY_TIMEOUT"] = "0"
    from assignment.benchmark import load_math500
    load_math500()  # Validate pinned data before any paid request.
    import numpy as np
    random.seed(p["seed"])
    np.random.seed(p["seed"])
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = ROOT / "assignment/runs" / f"{p['phase']}_steps{p['max_steps']}_seed{p['seed']}_{run_id}"
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "source_hashes.json", source_fingerprint())
    versions = {d.metadata["Name"]: d.version for d in importlib.metadata.distributions() if d.metadata["Name"]}
    write_json(output / "environment.json", {"python": sys.version, "platform": platform.platform(), "packages": versions})
    manifest = {"status": "running", "started_at_utc": stamp(), "upstream_commit": PLAN["upstream_commit"],
                "parameters": p, "model": model, "base_url": endpoint, "thinking": False,
                "sdk_retries": 0, "request_timeout_seconds": 90,
                "dataset": json.loads((ROOT / "assignment/data/manifest.json").read_text(encoding="utf-8"))}
    write_json(output / "run_manifest.json", manifest)
    import lits.lm.openai_chat as adapter
    ledger = Ledger(output / "api_calls.jsonl", p["call_limit"])
    original_request = adapter.request_with_network_retry
    original_init = adapter.OpenAIChatModel.__init__
    def init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.client = self.client.with_options(max_retries=0, timeout=90.0)
    adapter.OpenAIChatModel.__init__ = init
    adapter.request_with_network_retry = ledger.wrap(original_request)
    from lits.cli.search import main as search_main
    from lits.cli.eval_search import main as eval_main
    print(f"RUN_DIRECTORY {output}", flush=True)
    try:
        started = time.perf_counter()
        invoke(search_main, search_args(p, output, model))
        manifest["search_seconds"] = time.perf_counter() - started
        for i in range(p["count"]):
            facts_path = output / f"search_facts_{i}.json"
            facts = json.loads(facts_path.read_text(encoding="utf-8")) if facts_path.exists() else {}
            if facts.get("status") != "complete":
                raise RuntimeError(f"Search did not complete for planned question {i}")
        manifest["status"] = "search_complete"
        write_json(output / "run_manifest.json", manifest)
        ledger.phase = "evaluation"
        started = time.perf_counter()
        invoke(eval_main, ["lits-eval", "--result_dir", str(output), "--llm-eval", "none"])
        manifest["evaluation_seconds"] = time.perf_counter() - started
        metrics = summarize(output)
        evaluated = metrics["evaluation"]["upstream_results"]
        if evaluated is None or {x["idx"] for x in evaluated["examples"]} != set(range(p["count"])):
            raise RuntimeError("Evaluation did not cover all planned questions")
        if len(metrics["per_question_depth"]) != p["count"]:
            raise RuntimeError("Full-tree evidence is missing for a planned question")
        if metrics["max_observed_depth"] is not None and metrics["max_observed_depth"] > p["max_steps"]:
            raise RuntimeError("Observed tree depth exceeds configured cap")
        manifest["status"] = "complete"
        print(json.dumps({"status": "complete", "usage": metrics}, indent=2), flush=True)
    except BaseException as exc:
        manifest.update(status="incomplete", error_type=type(exc).__name__)
        summarize(output)
        raise
    finally:
        manifest["finished_at_utc"] = stamp()
        write_json(output / "run_manifest.json", manifest)
        adapter.request_with_network_retry = original_request
        adapter.OpenAIChatModel.__init__ = original_init


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["plan", "preflight", "run", "summarize"])
    parser.add_argument("--phase", choices=["smoke", "pilot", "formal"], default="smoke")
    parser.add_argument("--max-steps", type=int)
    parser.add_argument("--seed", type=int, choices=PLAN["study"]["seeds"], default=11)
    parser.add_argument("--call-limit", type=int)
    parser.add_argument("--run-dir", type=Path)
    args = parser.parse_args()
    os.chdir(ROOT)
    if args.command == "preflight":
        preflight()
    elif args.command == "summarize":
        if args.run_dir is None:
            parser.error("--run-dir is required for summarize")
        print(json.dumps(summarize(args.run_dir), indent=2))
    else:
        p = parameters(args.phase, args.max_steps, args.seed, args.call_limit)
        if args.command == "plan":
            print(json.dumps({"model": PLAN["model"], "parameters": p,
                              "real_api_calls": 0, "model_effect_comparison": "not measured"}, indent=2))
        else:
            run(p)


if __name__ == "__main__":
    main()
