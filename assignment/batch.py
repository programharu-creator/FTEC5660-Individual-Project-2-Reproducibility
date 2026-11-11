"""Run the nine fixed formal configurations concurrently; preserve every run."""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = json.loads((ROOT / "assignment/experiment_plan.json").read_text(encoding="utf-8"))


def write(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main():
    if not sys.flags.utf8_mode and os.name == "nt":
        raise SystemExit(subprocess.call([sys.executable, "-X", "utf8", "-m", "assignment.batch"]))
    os.chdir(ROOT)
    batch_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    directory = ROOT / "assignment/runs" / ("formal_batch_" + batch_id)
    directory.mkdir(parents=True, exist_ok=False)
    jobs = []
    for steps in PLAN["study"]["max_steps"]:
        for seed in PLAN["study"]["seeds"]:
            output = (directory / f"steps{steps}_seed{seed}.log").open("w", encoding="utf-8")
            command = [sys.executable, "-X", "utf8", "-m", "assignment.study", "run",
                       "--phase", "formal", "--max-steps", str(steps), "--seed", str(seed),
                       "--call-limit", "2000"]
            proc = subprocess.Popen(command, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)
            jobs.append({"max_steps": steps, "seed": seed, "process": proc, "log": output})
    started, last_report = time.monotonic(), 0
    stopped = None
    manifest = {"batch_id": batch_id, "concurrency": len(jobs), "status": "running",
                "cost_guard_usd": 3.0, "cost_guard_basis": "all input at $0.30/M, output at $1.20/M; conservative no-cache peak-rate guard",
                "pricing_reference": "https://api-docs.deepseek.com/quick_start/pricing/",
                "per_run_call_limit": 2000, "runtime_limit_seconds": 1800}
    write(directory / "batch_manifest.json", manifest)
    print("FORMAL_BATCH_STARTED " + batch_id, flush=True)
    try:
        while True:
            runs = [p for p in (ROOT / "assignment/runs").glob("formal_steps*")
                    if p.name.rsplit("_", 1)[-1] >= batch_id.replace("Z", "")]
            calls, input_tokens, output_tokens, completed_questions = 0, 0, 0, 0
            for run in runs:
                api = run / "api_calls.jsonl"
                if api.exists():
                    for line in api.read_text(encoding="utf-8").splitlines():
                        try:
                            rec = json.loads(line)
                        except json.JSONDecodeError:
                            continue  # A concurrently appended last line may be incomplete.
                        calls += 1
                        input_tokens += rec.get("usage", {}).get("prompt_tokens", 0)
                        output_tokens += rec.get("usage", {}).get("completion_tokens", 0)
                for facts in run.glob("search_facts_*.json"):
                    try:
                        completed_questions += json.loads(facts.read_text(encoding="utf-8")).get("status") == "complete"
                    except (json.JSONDecodeError, FileNotFoundError):
                        pass
            finished = sum(j["process"].poll() is not None for j in jobs)
            guard_value = input_tokens * 0.30 / 1e6 + output_tokens * 1.20 / 1e6
            manifest.update(completed_jobs=finished, completed_question_runs=completed_questions,
                input_tokens=input_tokens, output_tokens=output_tokens, api_calls=calls,
                no_cache_peak_rate_guard_usd=guard_value)
            write(directory / "batch_manifest.json", manifest)
            now = time.monotonic()
            if now - last_report >= 30 or finished == len(jobs):
                print(json.dumps({k:manifest[k] for k in ["completed_jobs", "completed_question_runs", "api_calls", "input_tokens", "output_tokens"]}), flush=True)
                last_report = now
            if finished == len(jobs):
                break
            if guard_value >= 3.0 or now - started >= 1800:
                stopped = "cost_guard" if guard_value >= 3.0 else "runtime_guard"
                for job in jobs:
                    if job["process"].poll() is None:
                        job["process"].terminate()
                break
            time.sleep(2)
    finally:
        for job in jobs:
            if job["process"].poll() is None:
                job["process"].terminate()
            job["process"].wait()
            job["log"].close()
        manifest.update(status="stopped" if stopped else "finished", stop_reason=stopped,
            elapsed_seconds=time.monotonic() - started,
            jobs=[{"max_steps":j["max_steps"],"seed":j["seed"],"exit_code":j["process"].returncode} for j in jobs])
        write(directory / "batch_manifest.json", manifest)
    print(json.dumps(manifest, indent=2), flush=True)
    return 0 if not stopped and all(j["process"].returncode == 0 for j in jobs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
