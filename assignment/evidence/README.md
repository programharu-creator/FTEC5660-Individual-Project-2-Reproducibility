# Experiment evidence

Nine complete formal runs are included, each with 30 question outputs. Source fingerprints are identical across selected runs.
The frozen assignment source used by those runs is local Git commit fea9659; upstream source is pinned separately in the plan.
Each folder contains configuration, run metadata, exact request usage, evaluated examples, per-question status and compact JSONL bundles of full trees and terminal nodes.
Bundles preserve original artifact filenames and JSON data. No model key is included.
The original incomplete attempts are listed in index.json and retained under excluded/.
A single Windows completion-file failure triggered one full retry of depth 10 / seed 11. This retry ran alone; the first batch used nine processes, so latency comparisons are descriptive.
Restore raw run directories without API calls with: python assignment/reporting/restore_evidence.py
Then install assignment/reporting/requirements-report.txt and run build_deliverables.py to regenerate the report and plots.
