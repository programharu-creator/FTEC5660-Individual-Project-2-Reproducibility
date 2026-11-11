# Debug diary

- Initial machine had Python 3.14 only and no Git on PATH. Prepared workspace-local Git and an isolated Python 3.12.12 environment.
- Upstream packaging includes large optional-use dependencies. The chosen workflow uses API calls, not local GPU inference. Removed the unused torch import in config.py and recorded a smaller API-path dependency lock.
- Upstream OpenAI-compatible wrapper sends a vLLM-specific thinking option to custom endpoints. Added an api.deepseek.com-specific mapping using DeepSeek's documented thinking field.
- The experiment-level default disables forced depth termination. Every experimental group explicitly enables the bound; otherwise changing max_steps would not reliably test the intended path-length budget.
- The paper's model/reward setup and our API-based setup differ. Treat the paper's numeric result as context, and measure depth changes within our fixed DeepSeek setup.
- API calls and paid experiments: pending.

- DeepSeek strict tool schemas require /beta. The adapter omits strict on the stable endpoint and retains the upstream schema and local validation; this supports answer voting without changing its selection rule.
- SearchNode.to_dict() omits depth. Depth metrics reconstruct parent-child depth from the saved full_tree artifacts and require one tree per planned question.

- First live smoke: all 11 DeepSeek requests succeeded (3614 input / 284 output tokens), then upstream checkpoint writing failed under Windows cp950 on a superscript character. Retained the incomplete run. The launcher now restarts in Python UTF-8 mode on Windows.
- Added a Git attribute preserving the downloaded dataset bytes; platform line-ending conversion must not invalidate its SHA256.
