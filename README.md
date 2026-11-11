# FTEC5660 - Individual Project 2 - Reproducibility

**Student:** SANG Yuchen  
**Student ID:** 1155262204  
**Course:** Agentic AI for Business and FinTech (FTEC5660)

This project runs the authors' LiTS MCTS workflow with DeepSeek and measures the effect of changing the maximum search depth. Code, the report, presentation slides and experimental evidence are ready. **The Zoom presentation video is pending and will be added later.**

## Submission materials

- [Report: 5 pages](assignment/deliverables/FTEC5660_LiTS_DeepSeek_Report.pdf)
- [Presentation slides: 10 pages](assignment/deliverables/FTEC5660_Presentation.pdf)
- [12-minute English recording script and screen directions](assignment/deliverables/RECORDING_SCRIPT_EN.md)
- [Printable recording script](assignment/deliverables/FTEC5660_Recording_Script_EN.pdf)
- [Assignment requirements checklist (Chinese)](assignment/deliverables/REQUIREMENTS_CHECK_CN.md)
- [Video link: pending recording](assignment/deliverables/VIDEO_LINK.md)
- [Trial-level CSV](assignment/deliverables/formal_trials.csv)
- [Results and sample variance](assignment/deliverables/formal_results.json)
- [Plot](assignment/deliverables/depth_comparison.png)
- [Raw evidence and restoration instructions](assignment/evidence/README.md)
- [Chinese experiment guide](assignment/README_CN.md)

## Experiment and results

The same ordered subset of 30 numeric-answer MATH500 questions was evaluated at maximum search depths of 1, 3 and 10, with three repeated runs per setting. The nine selected formal runs cover 270 question-runs on 30 distinct questions.

| Maximum steps | Accuracy, mean ± sample SD | Tokens per question, mean |
|---|---:|---:|
| 1 | 90.0% ± 0.0 percentage points | 8,461 |
| 3 | 90.0% ± 3.3 percentage points | 10,984 |
| 10 | 85.6% ± 5.1 percentage points | 11,373 |

The larger cap did not provide a consistent score improvement on this subset. One step refers to one external search action, which can contain a complete mathematical derivation. The 10-step group reached an observed maximum depth of 4, rather than executing 10 steps for every question.

These are the original checker's scores. A post-hoc audit found 16 format-only false negatives involving units or currency; the primary results were not rewritten. See [the audit](assignment/deliverables/format_audit.json). Timing is descriptive: one configuration was rerun alone after a Windows file-write failure, while the initial batch used nine processes.

## Scope and attribution

- [Original LiTS paper, v2](https://arxiv.org/html/2603.00631v2)
- [Original repository](https://github.com/xinzhel/lits-llm)
- Pinned upstream commit: 25e94d862cb4514c22d9a80a635e392461769df7.
- Original upstream documentation is preserved in [README_UPSTREAM.md](README_UPSTREAM.md).
- The original Apache 2.0 license is retained in [LICENSE](LICENSE).

The paper's Table 6 used a different model/reward setup and 100 questions. This study reproduces the API-compatible workflow under a substituted model; it does not claim a same-condition replication of the paper's 37% result or a causal comparison between the original model and DeepSeek.

The five-question pilot informed the final depth grid before formal execution. Pilot overlap, provider nondeterminism, the smaller ordered subset and model-based answer grouping are disclosed in the report. All nine selected formal runs have identical recorded source fingerprints; incomplete attempts are retained separately.

## Install and run

Use Python 3.12. From this repository's root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r assignment/requirements-api.lock.txt
.\.venv\Scripts\python.exe -m assignment.prepare_data
.\.venv\Scripts\python.exe -m assignment.study preflight
```

Preflight does not call a model. To run a paid experiment, copy assignment/.env.example to the root .env and set your own DEEPSEEK_API_KEY locally. Never commit that file.

```powershell
.\.venv\Scripts\python.exe -m assignment.study run --phase smoke
.\.venv\Scripts\python.exe -m assignment.study run --phase formal --max-steps 1 --seed 11
```

Repeat the formal command for depths 1, 3, 10 and local seeds 11, 22, 33. The API implementation uses fixed role-specific decoding settings; each outgoing request's parameters and usage are logged. Local seeds do not guarantee deterministic remote-model output.

## Inspect saved results without an API key

```powershell
python assignment/reporting/restore_evidence.py
python -m pip install -r assignment/reporting/requirements-report.txt
python assignment/reporting/build_deliverables.py
```

The evidence bundles contain full trees, terminal nodes, run status, numeric-checker outcomes and model-call usage. Source and dataset hashes are recorded. The fixed numeric dataset artifact is included and checked on load.

API keys, the local virtual environment, caches and uncurated raw-run folders are excluded from Git. The video will be added by updating the video-link document after recording.
