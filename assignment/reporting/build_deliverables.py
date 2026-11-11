"""Build the assignment report, plots, presentation PDF and evidence index from real runs."""
import csv
import ast
import re
import hashlib
import json
import math
import statistics as st
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assignment/deliverables"
PLAN = json.loads((ROOT / "assignment/experiment_plan.json").read_text(encoding="utf-8"))
GIT = ROOT.parent / ".runtime/lits-assignment-tools/git/cmd/git.exe"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def collect():
    rows, hashes = [], []
    for depth in PLAN["study"]["max_steps"]:
        for seed in PLAN["study"]["seeds"]:
            candidates = sorted((ROOT / "assignment/runs").glob(f"formal_steps{depth}_seed{seed}_*"))
            complete = [p for p in candidates if read(p / "run_manifest.json")["status"] == "complete"]
            if len(complete) != 1:
                raise RuntimeError(f"Expected exactly one complete formal run at depth={depth}, seed={seed}; found {len(complete)}")
            path = complete[0]
            manifest, usage = read(path / "run_manifest.json"), read(path / "usage_summary.json")
            results = usage["evaluation"]["upstream_results"]
            n = manifest["parameters"]["count"]
            if len(results["examples"]) != n or {x["idx"] for x in results["examples"]} != set(range(n)):
                raise RuntimeError("Incomplete or duplicated evaluation denominator")
            if usage["max_observed_depth"] > depth:
                raise RuntimeError("Depth bound violated")
            ledger = [json.loads(x) for x in (path / "api_calls.jsonl").read_text(encoding="utf-8").splitlines()]
            if any(x["status"] != "ok" for x in ledger):
                raise RuntimeError("A formal run contains provider failures")
            hashes.append(read(path / "source_hashes.json"))
            row = {
                "max_steps": depth, "local_seed": seed, "n": n,
                "correct": sum(x["correct"] for x in results["examples"]), "accuracy": results["accuracy"],
                "search_seconds": manifest["search_seconds"], "evaluation_seconds": manifest["evaluation_seconds"],
                "search_calls": usage["search"]["calls"], "evaluation_calls": usage["evaluation"]["calls"],
                "input_tokens": sum(x.get("usage", {}).get("prompt_tokens", 0) for x in ledger),
                "output_tokens": sum(x.get("usage", {}).get("completion_tokens", 0) for x in ledger),
                "mean_max_observed_depth": usage["mean_max_observed_depth"],
                "max_observed_depth": usage["max_observed_depth"], "run_directory": path.name,
                "served_models": usage["served_models"],
            }
            row["seconds_per_question"] = (row["search_seconds"] + row["evaluation_seconds"]) / n
            row["calls_per_question"] = (row["search_calls"] + row["evaluation_calls"]) / n
            row["tokens_per_question"] = (row["input_tokens"] + row["output_tokens"]) / n
            format_cases = []
            patterns = {
                14: r"78(?:\.0+)?(?:\s*(?:dollars?|USD))?",
                19: r"72(?:\.0+)?\s*(?:\u00b0|degrees?)",
                22: r"12(?:\.0+)?\s*(?:cm|centimet(?:er|re)s?)",
            }
            for line in (path / "eval.log").read_text(encoding="utf-8").splitlines():
                match = re.search(r"\[(\d+)\] Pred=(.*), Truth=(.*), Correct=(True|False)$", line)
                if not match or match[4] != "False" or int(match[1]) not in patterns:
                    continue
                predicted, truth = ast.literal_eval(match[2]), ast.literal_eval(match[3])
                clean = str(predicted).replace("\\$", "$").strip().strip("$").strip()
                clean = clean.replace(r"^\circ", "\u00b0").replace(r"\circ", "\u00b0")
                if re.fullmatch(patterns[int(match[1])], clean, re.IGNORECASE):
                    format_cases.append({"idx": int(match[1]), "prediction": predicted, "reference": truth})
            row["format_false_negatives"] = len(format_cases)
            row["format_cases"] = format_cases
            rows.append(row)
    if any(h != hashes[0] for h in hashes[1:]):
        raise RuntimeError("Formal groups used different recorded source files/settings")
    groups = []
    for depth in PLAN["study"]["max_steps"]:
        selected = [x for x in rows if x["max_steps"] == depth]
        group = {"max_steps": depth, "trials": len(selected), "questions_per_trial": selected[0]["n"]}
        for key in ["accuracy", "seconds_per_question", "calls_per_question", "tokens_per_question",
                    "input_tokens", "output_tokens", "mean_max_observed_depth"]:
            values = [x[key] for x in selected]
            group[key + "_mean"] = st.mean(values)
            group[key + "_sd"] = st.stdev(values)
            group[key + "_variance"] = st.variance(values)
        group["max_observed_depth"] = max(x["max_observed_depth"] for x in selected)
        groups.append(group)
    return rows, groups, hashes[0]


def mean_sd(group, field, scale=1, digits=1):
    return f"{group[field+'_mean']*scale:.{digits}f} +/- {group[field+'_sd']*scale:.{digits}f}"


def build_plots(groups):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))
    x = list(range(len(groups)))
    colors = ["#156082", "#2a9d8f", "#e9a23b"]
    specs = [("accuracy", 100, "Accuracy (%)"), ("tokens_per_question", 1, "Tokens / question"),
             ("seconds_per_question", 1, "Wall seconds / question")]
    for ax, (field, scale, label) in zip(axes, specs):
        means = [g[field+"_mean"]*scale for g in groups]
        sd = [g[field+"_sd"]*scale for g in groups]
        ax.bar(x, means, color=colors, width=0.65, yerr=sd, capsize=5)
        ax.set_xticks(x, [str(g["max_steps"]) for g in groups])
        ax.set_xlabel("Maximum search steps")
        ax.set_ylabel(label)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)
        if field == "accuracy":
            ax.set_ylim(0, 105)
        for i, value in enumerate(means):
            ax.text(i, value + sd[i] + max(means)*0.025, f"{value:.1f}", ha="center", fontsize=9)
    fig.suptitle("LiTS + DeepSeek: fixed 30 questions, three repetitions per setting", fontsize=12, y=1.02)
    fig.text(0.5, -0.035, "Error bars: sample standard deviation across repeated runs. Tokens and time include search + answer voting.",
             ha="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "depth_comparison.png", dpi=180, bbox_inches="tight")
    fig.savefig(OUT / "depth_comparison.pdf", bbox_inches="tight")
    plt.close(fig)


def source_refs():
    return [
        ("LiTS paper v2 (Table 6 and setup)", "https://arxiv.org/html/2603.00631v2"),
        ("Pinned LiTS source", "https://github.com/xinzhel/lits-llm/tree/" + PLAN["upstream_commit"]),
        ("Pinned numeric dataset", "https://huggingface.co/datasets/xinzhel/math500-float/tree/" + PLAN["dataset"]["revision"]),
        ("DeepSeek thinking control", "https://api-docs.deepseek.com/guides/thinking_mode/"),
        ("DeepSeek tool API", "https://api-docs.deepseek.com/guides/tool_calls/"),
    ]


def build_report(rows, groups):
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    for name, filename in [("Body", "times.ttf"), ("BodyBold", "timesbd.ttf"), ("Sans", "arial.ttf")]:
        pdfmetrics.registerFont(TTFont(name, str(Path("C:/Windows/Fonts") / filename)))
    style = {
        "title": ParagraphStyle("title", fontName="BodyBold", fontSize=22, leading=26, textColor=colors.HexColor("#156082"), spaceAfter=14),
        "head": ParagraphStyle("head", fontName="BodyBold", fontSize=14, leading=18, spaceBefore=10, spaceAfter=7),
        "body": ParagraphStyle("body", fontName="Body", fontSize=10.5, leading=14, spaceAfter=8),
        "small": ParagraphStyle("small", fontName="Body", fontSize=8.5, leading=11, spaceAfter=6),
        "cell": ParagraphStyle("cell", fontName="Body", fontSize=9, leading=11),
    }
    story = []
    def p(text, kind="body"):
        story.append(Paragraph(text, style[kind]))
    def heading(text):
        p(text, "head")
    def table(data, widths):
        values = [[Paragraph(escape(str(v)), style["cell"]) for v in row] for row in data]
        t = Table(values, colWidths=widths, repeatRows=1, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e7f1f5")),
            ("LINEBELOW", (0,0), (-1,0), 0.7, colors.HexColor("#156082")),
            ("LINEBELOW", (0,-1), (-1,-1), 0.4, colors.lightgrey),
            ("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING",(0,0),(-1,-1),6),
            ("RIGHTPADDING",(0,0),(-1,-1),6), ("TOPPADDING",(0,0),(-1,-1),7),
            ("BOTTOMPADDING",(0,0),(-1,-1),7),
        ]))
        story.append(t)
        story.append(Spacer(1,10))
    baseline = next(g for g in groups if g["max_steps"] == 10)
    best = max(groups, key=lambda g:g["accuracy_mean"])
    cheapest = min(groups, key=lambda g:g["tokens_per_question_mean"])
    total_calls = sum(r["search_calls"] + r["evaluation_calls"] for r in rows)

    p("Reproducing LiTS with DeepSeek", "title")
    p("The effect of maximum search depth on a small MATH500 benchmark", "head")
    p("FTEC5660 - Agentic AI for Business and FinTech<br/>Name: SANG Yuchen &nbsp;&nbsp; Student ID: 1155262204")
    p("Reproducibility report | 4 November 2026 | Individual assignment", "small")
    heading("1. Objective and scope")
    p("This study runs the authors' LiTS implementation of MCTS mathematical reasoning using an accessible DeepSeek API model. It reproduces a runnable agentic workflow, then changes one experimental factor: the maximum number of steps on a search-tree path. The measured outcomes are accuracy, token usage, model-call count, wall time and observed tree depth.")
    p("The numerical reference is LiTS paper v2, Table 6: ReST (MCTS) reports 37% on 100 numerical-answer MATH500 questions using Llama3-8B and the paper's reward setup. Our DeepSeek model, API-based GenerativePRM, current repository snapshot, smaller question prefix and bounded-search settings differ. Our numbers therefore do not constitute a strict replication of that 37% result or a causal estimate of the benefit of replacing Llama3 with DeepSeek.")
    heading("Main measured findings")
    p(f"The default-depth group (10 steps) achieved {mean_sd(baseline,'accuracy',100)}% accuracy across three runs. The highest mean accuracy was {best['accuracy_mean']*100:.1f}%, shared by settings {[g['max_steps'] for g in groups if abs(g['accuracy_mean']-best['accuracy_mean'])<1e-10]}; this descriptive comparison is specific to these 30 questions. The lowest measured token use was at depth {cheapest['max_steps']}. All nine formal runs completed, covering 270 question-runs on 30 distinct questions, with {total_calls:,} model calls in total.")
    heading("What was reproduced")
    p("The fixed local dataset loaded into the repository's registered MATH500 task; its ConcatPolicy, ConcatTransition and GenerativePRM executed real MCTS searches; saved terminal answers were grouped through the repository's voting workflow and checked using the author's deterministic numeric checker. The full trees, configurations and per-call usage provide inspectable evidence.")
    story.append(PageBreak())

    heading("2. Setup and controlled experimental design")
    table([
        ["Item", "Fixed setting"],
        ["Source", PLAN["upstream_commit"]],
        ["Environment", "Windows; isolated CPython 3.12.12; exact API-path dependency lock"],
        ["Dataset", "xinzhel/math500-float; test.jsonl; 316 numeric rows; first 30 rows in original order"],
        ["Dataset revision", PLAN["dataset"]["revision"]],
        ["Model / endpoint", "deepseek-flash / https://api.deepseek.com; internal thinking disabled"],
        ["Search", "MCTS; 10 iterations; branching factor 3; rollout length 2; simulation branching 1"],
        ["Depth experiment", "max_steps = 1, 3, 10; forced depth limit enabled in every group"],
        ["Scoring and termination", "GenerativePRM: correctness samples 2, usefulness samples 1; termination samples 3"],
        ["Generation / repeats", "Policy output cap 512 tokens; unchanged role-specific decoding; local seeds 11, 22, 33"],
        ["Execution", "Initial nine-process batch; one full retry alone; same source fingerprints; SDK retries off; timeout 90 s"],
    ], [105, 402])
    p("Temperature is not one universal scalar in LiTS: generation, scoring, termination checks and voting use their existing role-specific values. Every outgoing request records its temperature, top_p, max_tokens and thinking payload. Recorded requests include top_p values 0.95 and 1.0 rather than one global value. Local Python/NumPy seeds are set; no claim is made that the remote model is seed-deterministic.", "small")
    heading("Pilot and design freeze")
    p("A one-question smoke run verified end-to-end execution. A separate five-question pilot scored 4/5 and reached maximum tree depths [1, 1, 1, 3, 1]. Before running any formal trial, the planned grid was changed from [5, 10, 15] to [1, 3, 10], so the experiment includes a short binding budget and the default-depth comparison. This decision and its earlier grid are recorded in the plan and Git history. The pilot overlaps with the formal prefix; this is an exploratory study, not an untouched held-out evaluation.")
    story.append(PageBreak())

    heading("3. Formal results")
    p("Each row below is the mean and sample standard deviation across three completed runs, each using the same 30 questions. Token usage and wall time include both search and final answer voting. Correctness is numeric checking after extraction; failed or unfinished setup runs are not included in these denominators.")
    table([["Max steps", "Accuracy (%)", "Calls / question", "Tokens / question", "Seconds / question"]] + [
        [g["max_steps"], mean_sd(g,"accuracy",100), mean_sd(g,"calls_per_question"),
         mean_sd(g,"tokens_per_question",digits=0), mean_sd(g,"seconds_per_question")]
        for g in groups], [60,110,105,120,112])
    story.append(Image(str(OUT/"depth_comparison.png"), width=500, height=172))
    heading("Observed depth")
    table([["Configured cap", "Mean maximum depth per question", "Deepest observed node"]] + [
        [g["max_steps"],mean_sd(g,"mean_max_observed_depth",digits=2),g["max_observed_depth"]] for g in groups],
        [110,250,147])
    p("All saved tree depths were checked against their configured cap. Depths are reconstructed from full-tree child links, rather than inferred from model-call count. The number of calls can greatly exceed the path depth because each expansion samples alternatives and evaluates reasoning steps.")
    p("These error bars summarize repeat-to-repeat variation on one fixed small dataset. They are not population confidence intervals. Hosted API load and concurrency affect wall time. The initial batch ran nine processes; the depth-10/seed-11 replacement ran alone after the file-write failure. Timing is descriptive and not a controlled latency comparison across identical load conditions.")
    story.append(PageBreak())

    heading("4. Trial-level evidence")
    table([["Cap", "Local seed", "Correct / 30", "Accuracy", "Search calls", "Vote calls", "Max depth"]] + [
        [r["max_steps"],r["local_seed"],f"{r['correct']}/{r['n']}",f"{r['accuracy']*100:.1f}%",
         r["search_calls"],r["evaluation_calls"],r["max_observed_depth"]] for r in rows],
         [40,65,90,70,85,80,77])
    heading("Metric definitions")
    p("<b>Accuracy:</b> correct predictions divided by all 30 planned questions in a completed run. An empty or missing final answer is incorrect. A run interrupted by an API, resource or artifact error is marked incomplete and retained separately, rather than silently shrinking the denominator.")
    p("<b>Tokens:</b> provider-reported prompt_tokens plus completion_tokens, aggregated from api_calls.jsonl. Search and voting totals remain separately available. Input-cache details are preserved in the raw usage fields. Provider errors are recorded and abort the run instead of becoming model mistakes.")
    p("<b>Time:</b> elapsed time around the search command plus its evaluation command, divided by 30. <b>Depth:</b> the largest parent-child distance from the root for each question. <b>Variability:</b> sample SD and sample variance over the three repeated runs, with variance included in the machine-readable summary.")
    heading("Post-hoc scoring audit")
    count = sum(r["format_false_negatives"] for r in rows)
    p(f"A manual audit identified {count} format-only false negatives across the 270 formal question-runs in three known tasks. Examples are a 72-degree rotation predicted as '72 degrees' or '72&#176;' against reference '72', profit '$78' against '78', and side length '12 cm' against '12'. The questions explicitly request these units. The original checker does not consistently strip units or currency from predictions.")
    p("The primary accuracies above remain unchanged. This diagnostic was discovered after execution and is not a replacement endpoint or a basis for selecting runs. It shows that the reported scores measure output formatting as well as numerical problem solving; small accuracy differences should not automatically be attributed to reasoning quality.")
    heading("Interpreting the modification")
    p("Changing max_steps affects LiTS's external search budget and its last-step instruction. It does not set the number of arithmetic operations or the model's internal reasoning tokens. In the pilot, the model often returned a complete derivation within one generated action. Consequently, a shallow tree can still contain substantial reasoning, and deeper search can add scoring/call cost without guaranteeing a better final answer.")
    p("No result was selected by looking at the reference answer: references are reserved for checking. The repository's generative reward model and answer grouping are themselves model-based, however, and can introduce errors or preferences.")
    story.append(PageBreak())

    heading("5. Debug diary and adaptations")
    p("<b>Environment:</b> the machine initially had Python 3.14 and no Git on PATH. A workspace-local Git installation and separate Python 3.12.12 environment were prepared. Only the API mathematics path was installed; local GPU, SQL, geospatial and memory functionality is outside the tested scope. An unused torch import in config.py was removed.")
    p("<b>Endpoint compatibility:</b> the wrapper originally sent vLLM-specific thinking options to all custom endpoints. It now sends DeepSeek's thinking.type field. DeepSeek's stable tool endpoint omits the beta-only strict flag while preserving the schema and LiTS's local validation. The same adapter is used in every formal group.")
    p("<b>Windows artifact failure:</b> the first live attempt completed 11 requests but failed while writing a superscript character under cp950. The failed run was retained and excluded from accuracy statistics. The launcher now uses UTF-8. A subsequent restart failure occurred before any API request; subprocess waiting was corrected. The successful smoke and all formal trials use the repaired path. One initial depth-10/seed-11 formal attempt failed during an atomic completion-marker replacement (WinError 5) after writing the search artifacts. That incomplete attempt was preserved, excluded from the main table, and the entire configuration was rerun once without changing the experimental source. The other eight groups were retained. Concurrent Windows state-file monitoring is a possible contributor, not a proven cause.")
    p("<b>Version control and evidence:</b> source and dataset revisions are fixed; the dataset hash is checked on load and its byte representation is protected from Git newline conversion. Every run writes source hashes, dependency versions, parameters, trees, per-call usage and a completion status. The .env key is ignored by Git and excluded from all submission artifacts.")
    heading("6. Conclusions and limitations")
    p(f"The API-backed LiTS workflow is runnable under the recorded conditions. At default depth 10 its measured accuracy was {mean_sd(baseline,'accuracy',100)}%. The step-budget experiment demonstrates how to measure the accuracy/resource tradeoff using one isolated configuration change; the tables report the measured effect without treating the paper's different-model result as an equivalent baseline.")
    p("The main limits are the small, ordered 30-question subset; three repetitions on the same tasks; pilot overlap; an evolving remote model alias; a different reward-model setup from the paper; model-based answer grouping; and strict numeric normalization that may not recognize every equivalent expression. Results should not be generalized to all MATH500 questions or used to claim that DeepSeek universally outperforms the original model.")
    heading("Reproduction commands")
    p("See assignment/README_CN.md. Rebuild the Python environment from requirements-api.lock.txt; prepare or verify the fixed data; place the key only in .env; run the preflight; then execute assignment.study with the saved phase, maximum step count and local seed. Raw run artifacts remain locally available; selected formal evidence is included in the submission package.", "small")
    heading("References")
    for title, url in source_refs():
        p(f'{escape(title)}: <link href="{url}" color="#156082">{escape(url)}</link>',"small")

    def page_footer(canvas, doc):
        canvas.setFont("Body",8)
        canvas.setFillColor(colors.HexColor("#667085"))
        canvas.drawString(44,25,"FTEC5660 | LiTS + DeepSeek reproducibility")
        canvas.drawRightString(A4[0]-44,25,str(doc.page))
    pdf = OUT / "FTEC5660_LiTS_DeepSeek_Report.pdf"
    doc=SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=40,bottomMargin=42,
                         title="Reproducing LiTS with DeepSeek",author="SANG Yuchen")
    doc.build(story,onFirstPage=page_footer,onLaterPages=page_footer)
    import pymupdf
    with pymupdf.open(pdf) as pages:
        if len(pages)>10:
            raise RuntimeError(f"Report exceeds page limit: {len(pages)}")
        pages[0].get_pixmap(matrix=pymupdf.Matrix(1,1)).save(OUT/"report_preview_1.png")
        return len(pages)


def build_slides(groups):
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.utils import ImageReader
    from textwrap import wrap
    width,height=960,540
    c=canvas.Canvas(str(OUT/"FTEC5660_Presentation.pdf"),pagesize=(width,height))
    baseline=next(g for g in groups if g["max_steps"]==10)
    slides=[
        ("LiTS + DeepSeek reproducibility",[
            "FTEC5660 | SANG Yuchen | 1155262204",
            "Question: how does maximum search depth affect accuracy and resource use?",
            "One fixed model; one fixed 30-question subset; three repeated runs."]),
        ("Project and reproduction target",[
            "Run the authors' MCTS workflow for numerical-answer MATH500 tasks.",
            "Policy proposes reasoning actions; transition builds a trajectory; reward scores it.",
            "Paper Table 6 is context: our model, reward setup and sample size differ."]),
        ("Fixed source, data and model",[
            "Pinned Git commit and Hugging Face dataset revision; SHA256 verified.",
            "CPython 3.12.12, API-only dependencies, DeepSeek Flash, thinking disabled.",
            "Per-request parameters, usage and model alias recorded; no keys in Git."]),
        ("Controlled modification",[
            "Maximum steps = 1, 3, 10; all groups enforce the same depth bound.",
            "Other controls: 10 MCTS iterations; branching 3; rollout 2; scoring fixed.",
            "Pilot informed the depth grid before formal experiments; overlap is disclosed."]),
        ("Measured results",[
            f"Depth {g['max_steps']}: accuracy {mean_sd(g,'accuracy',100)}%; "
            f"tokens/question {g['tokens_per_question_mean']:.0f}; "
            f"seconds/question {g['seconds_per_question_mean']:.1f}." for g in groups]),
        ("Accuracy, tokens and time",[]),
        ("Why a step is not a token budget",[
            "One generated action may contain a complete multi-operation derivation.",
            "The cap also changes the repository's final-step instruction.",
            "A larger external search budget does not guarantee better final answers."]),
        ("Blockers and fixes",[
            "Prepared an isolated compatible Python environment.",
            "Adapted DeepSeek thinking and stable tool-schema options.",
            "Fixed Windows UTF-8 artifact writing; preserved incomplete attempts."]),
        ("Evidence and limitations",[
            "Nine complete formal runs; 270 question-runs; only 30 distinct questions.",
            "Same-source fingerprints, trees, configs, numeric checker and raw usage saved.",
            "Strict scoring penalizes units/currency; small sample and pilot overlap limit conclusions."]),
        ("Reproduce and conclude",[
            f"Default depth 10: {mean_sd(baseline,'accuracy',100)}% on this subset.",
            "Follow assignment/README_CN.md; inspect run_manifest and usage_summary.",
            "Submit the report, GitHub repository link and a Zoom recording under 15 minutes."]),
    ]
    script=[]
    for number,(title,bullets) in enumerate(slides,1):
        c.setFillColor(colors.HexColor("#f7fafc")); c.rect(0,0,width,height,fill=1,stroke=0)
        c.setFillColor(colors.HexColor("#156082")); c.rect(0,height-12,width,12,fill=1,stroke=0)
        c.setFont("Helvetica-Bold",27); c.drawString(48,height-74,title)
        if number==6:
            c.drawImage(ImageReader(str(OUT/"depth_comparison.png")),35,110,width=890,height=280,preserveAspectRatio=True,mask="auto")
        else:
            y=height-145
            c.setFillColor(colors.HexColor("#243746"))
            for bullet in bullets:
                lines=wrap(bullet,width=79)
                c.setFont("Helvetica",18)
                for i,line in enumerate(lines):
                    c.drawString(55 if i else 48,y,("- " if i==0 else "  ")+line)
                    y-=28
                y-=18
        c.setFont("Helvetica",10); c.setFillColor(colors.HexColor("#667085"))
        c.drawString(48,28,"LiTS reproducibility | All numbers come from completed formal runs")
        c.drawRightString(width-40,28,f"{number} / {len(slides)}")
        c.showPage()
        script.append(f"## Slide {number}: {title}\n\n" + "\n".join("- "+b for b in bullets) + "\n")
    c.save()
    (OUT/"PRESENTATION_SCRIPT.md").write_text(
        "# Recording guide (target 10-12 minutes; maximum 15)\n\n"
        "Share this PDF in Zoom, record yourself explaining the results, "
        "and submit an accessible recording link. These files are presentation materials, not a recorded video.\n\n"
        + "\n".join(script),encoding="utf-8")


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows,groups,hashes=collect()
    output={"generated_at_utc":datetime.now(timezone.utc).isoformat(),"trials":rows,"groups":groups,
            "source_fingerprints_identical":True,"formal_trials":len(rows),
            "distinct_questions":PLAN["dataset"]["formal_count"],"question_runs":sum(r["n"] for r in rows)}
    (OUT/"formal_results.json").write_text(json.dumps(output,indent=2)+"\n",encoding="utf-8")
    fields=[k for k in rows[0] if k not in ("served_models","format_cases")]
    with (OUT/"formal_trials.csv").open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields); writer.writeheader()
        writer.writerows({k:r[k] for k in fields} for r in rows)
    (OUT/"format_audit.json").write_text(json.dumps([
        {"max_steps":r["max_steps"],"local_seed":r["local_seed"],"cases":r["format_cases"]}
        for r in rows],indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    build_plots(groups)
    pages=build_report(rows,groups)
    build_slides(groups)
    print(json.dumps({"report_pages":pages,"formal_trials":len(rows),"groups":groups},indent=2))


if __name__=="__main__":
    main()
