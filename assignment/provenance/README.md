# Source snapshots and browser publication

The experiments ran locally on 4 November 2026. Materials were published on 11 November 2026 by forking the authors' repository and uploading staged changes through GitHub's browser interface on the restricted company computer. The upstream history is retained. Web publication did not run or change the experiments.

GitHub creates new commit IDs for browser uploads. The original local IDs in run documentation identify the original snapshots; the public web commits provide corresponding file snapshots. `web_upload_commits.json` maps these stages and records their Git tree IDs. Matching tree IDs mean that all tracked paths and file bytes at those stages are identical, even though commit IDs and publication dates differ.

The formal experiments used local snapshot `fea9659d162caef645eda0a24b648f5eb70c15dd`. The same complete file tree is available in public commit [`9f5b3e484860de200a976843c13cc92d7dc9ea00`](https://github.com/programharu-creator/FTEC5660-Individual-Project-2-Reproducibility/commit/9f5b3e484860de200a976843c13cc92d7dc9ea00): tree `e44f2aed7d94c45665a65dfd183cd59b18c6672a`.

The results stage was divided into an evidence commit and a report/presentation commit to stay within the browser's file-count limit. Equality is checked after the complete stage, rather than after its intermediate evidence-only commit. A later stage preserves the original evidence byte representation across Windows line endings; the final evidence hashes match `assignment/evidence/FILE_SHA256.json`.

The final publication-status and provenance documents were added after these snapshots. Their addition does not alter the formal run artifacts, scores, or experimental source snapshot. The video remains pending until the student records it and provides an accessible Zoom presentation link.
