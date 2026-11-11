# Recording guide (target 10-12 minutes; maximum 15)

Share this PDF in Zoom, record yourself explaining the results, and submit an accessible recording link. These files are presentation materials, not a recorded video.

## Slide 1: LiTS + DeepSeek reproducibility

- FTEC5660 | SANG Yuchen | 1155262204
- Question: how does maximum search depth affect accuracy and resource use?
- One fixed model; one fixed 30-question subset; three repeated runs.

## Slide 2: Project and reproduction target

- Run the authors' MCTS workflow for numerical-answer MATH500 tasks.
- Policy proposes reasoning actions; transition builds a trajectory; reward scores it.
- Paper Table 6 is context: our model, reward setup and sample size differ.

## Slide 3: Fixed source, data and model

- Pinned Git commit and Hugging Face dataset revision; SHA256 verified.
- CPython 3.12.12, API-only dependencies, DeepSeek Flash, thinking disabled.
- Per-request parameters, usage and model alias recorded; no keys in Git.

## Slide 4: Controlled modification

- Maximum steps = 1, 3, 10; all groups enforce the same depth bound.
- Other controls: 10 MCTS iterations; branching 3; rollout 2; scoring fixed.
- Pilot informed the depth grid before formal experiments; overlap is disclosed.

## Slide 5: Measured results

- Depth 1: accuracy 90.0 +/- 0.0%; tokens/question 8461; seconds/question 14.6.
- Depth 3: accuracy 90.0 +/- 3.3%; tokens/question 10984; seconds/question 16.9.
- Depth 10: accuracy 85.6 +/- 5.1%; tokens/question 11373; seconds/question 17.5.

## Slide 6: Accuracy, tokens and time



## Slide 7: Why a step is not a token budget

- One generated action may contain a complete multi-operation derivation.
- The cap also changes the repository's final-step instruction.
- A larger external search budget does not guarantee better final answers.

## Slide 8: Blockers and fixes

- Prepared an isolated compatible Python environment.
- Adapted DeepSeek thinking and stable tool-schema options.
- Fixed Windows UTF-8 artifact writing; preserved incomplete attempts.

## Slide 9: Evidence and limitations

- Nine complete formal runs; 270 question-runs; only 30 distinct questions.
- Same-source fingerprints, trees, configs, numeric checker and raw usage saved.
- Strict scoring penalizes units/currency; small sample and pilot overlap limit conclusions.

## Slide 10: Reproduce and conclude

- Default depth 10: 85.6 +/- 5.1% on this subset.
- Follow assignment/README_CN.md; inspect run_manifest and usage_summary.
- Submit the report, GitHub repository link and a Zoom recording under 15 minutes.
