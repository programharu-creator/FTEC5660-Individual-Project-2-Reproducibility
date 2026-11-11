# Report outline — fill with measured results only

Name:
Student ID:
Course: FTEC5660
Title: Reproducing LiTS with DeepSeek: the effect of maximum search depth
Maximum length: 10 pages

1. Project and target: repository API-based MATH500 MCTS workflow; cite paper v2 and pinned upstream commit.
2. Setup: Python, Windows, API-only dependency lock, dataset revision/SHA256, model identifier, endpoint, thinking and decoding settings. Never include a key.
3. Scope differences: paper Table 6 used 100 numeric questions, Llama3-8B and a different reward setup. Our API/scoring adaptations and smaller subset prevent direct numeric equivalence.
4. Reproduction: one completed default-depth run, actual measured outputs, comparison to the claimed workflow and contextual paper result.
5. Controlled modification: max_steps only, with model, data, branching, iterations, scoring, termination and evaluation fixed.
6. Results: accuracy = correct / all planned questions for a complete run; completion rate; per-question wall time; input/output tokens; calls; max/mean observed depth. Separate search and answer-voting usage.
7. Repeat 3 times and report mean and sample variance (or SD, explicitly labelled). Distinguish pilot/formal runs. Do not pool incomplete/aborted runs or silently drop failed questions.
8. Debug diary: environment, endpoint compatibility, data/version issues, and fixes, with evidence.
9. Conclusions and limitations: small sample, API nondeterminism, model alias changes, reward-model mismatch and no original-model causal comparison.

Results pending. No accuracy, token-cost or timing result has been measured yet.
