"""Build a self-contained presentation specification and narration. Author: eula.

Uses the Python standard library and existing report tools. The PowerPoint
renderer uses the installed Microsoft Office application, without installation.
"""
from pathlib import Path
import json
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assignment/deliverables"
CACHE = ROOT / "assignment/.cache/presentation-redesign"
AUTHOR = "eula"
W, H = 1440, 810
BG, NAVY, TEAL, INK = "F5F3ED", "142536", "087F83", "203344"
MUTED, LINE, MINT, ORANGE = "617382", "DCE3E3", "E2F1EB", "BA633E"

# The same glossary is applied to both versions, with longer phrases matched first.
# Counts describe this fixed glossary, rather than every possible technical term.
TERMS = [
    "Monte Carlo Tree Search", "API based generative reward component", "reward component",
    "transition component", "generative reward", "numeric checking", "numeric checker",
    "sample standard deviation", "standard deviation", "model based", "held out",
    "source hashes", "checksum", "Git commit", "Hugging Face", "dataset", "upstream",
    "Python", "API", "MCTS", "ReST", "MATH500", "LiTS", "DeepSeek", "GitHub",
    "trajectory", "trajectories", "policy", "terminal", "endpoint", "decoding",
    "seed", "seeds", "branching factor", "rollout", "forced termination",
    "token", "tokens", "preflight", "dependency lock", "manifest", "normalization",
    "Unicode", "UTF", "torch", "beta", "schema", "atomic", "completion marker",
    "model wrapper", "remote model alias", "artifact", "artifacts", "configuration",
]

TIMES = ["00:00-00:40", "00:40-01:35", "01:35-02:35", "02:35-03:40", "03:40-04:35",
         "04:35-05:30", "05:30-06:25", "06:25-07:30", "07:30-08:40", "08:40-10:00"]
TITLES = ["Testing LiTS with DeepSeek", "What I reproduced", "One setting changes across three groups",
          "Accuracy across all nine runs", "Text use rises with the search limit",
          "One search step can include a full calculation", "Repairs that made the experiment run",
          "Saved records show how the experiment ran", "Answer formatting affects the score",
          "Reproduce the test and use the evidence"]
NARRATION = [
    "Hello, my name is SANG Yuchen, and this presentation explains my FTEC5660 reproducibility project, which uses LiTS with DeepSeek to solve a small set of mathematics questions. I studied how the allowed number of search steps affects correct answers and resource use, using thirty questions and repeating each setting three times. The results show that a shorter setting achieved strong scores with lower token use, and the following slides contain the setup, measured results and saved records, with all nine completed runs included in the final comparison.",
    "LiTS works through several stages, proposing possible solutions, checking their quality and choosing an answer from the available results. This process makes it suitable for studying how additional search affects performance. The paper reports thirty seven percent accuracy on one hundred mathematics questions, while my version uses DeepSeek and thirty questions with a different scoring setup. Those differences require care when interpreting the numbers, so my controlled comparison focuses on the three search limits within the same setup. The diagram and comparison cards show the workflow I reproduced and the conditions that define this smaller study, and the original code remains responsible for producing and checking the answers.",
    "The three groups allow one, three or ten search steps, with ten serving as the starting setting for comparison. Each group receives the same thirty questions in the same order, and the program repeats the test three times while keeping the other settings fixed. The code shown here makes the search limit apply in every group, which matters because a setting needs to affect actual program behavior before its results can be interpreted. I also recorded the source version, data version and model settings so that another reader can identify the materials used for these runs, including the five preparation questions that also appear in the final set.",
    "The results table contains all nine completed runs, with every score calculated from thirty planned questions and missing answers counted as incorrect. The average accuracy is ninety percent at limits one and three, compared with eighty five point six percent at limit ten. The values beside each average show how much the scores varied across the three runs, and the right hand table shows the individual correct answer counts. These results suggest limited benefit from allowing more steps on this small question set, while a larger evaluation would help establish how well this pattern applies to other questions, and every completed run contributes equally to the reported averages.",
    "The model service counts text use in tokens, which are pieces of text processed when reading questions and producing answers. The recorded average rises from about eight thousand five hundred per question at limit one to about eleven thousand four hundred at limit ten, giving the shorter setting roughly twenty six percent lower use. Recorded time also increases, although the runs used different levels of simultaneous activity because one test was repeated alone after a file saving failure. I therefore use time as a descriptive result and treat the text counts as the clearer resource comparison, with searching and final answer selection both included in the saved counts.",
    "The example on this slide helps explain why a short search can work well. One question asks how many positive whole numbers divide one hundred and ninety six, and the saved response completes the calculation inside a single generated action. A search step can therefore contain several mathematical operations. The recorded depth also shows that the group allowing ten steps reached a maximum of four, because many answers finished earlier. Changing the limit also changes when the program asks for a final answer, so the measured effect includes that instruction as well as the permitted search length, with the displayed calculation preserving the outcome of the saved response.",
    "Several practical repairs helped the program run successfully on this computer. I prepared a suitable Python environment, adjusted the settings sent to DeepSeek, and changed how the program saves special characters on Windows. A later attempt failed while replacing a completion file, so I kept that incomplete attempt and repeated the entire affected test once with the same source and settings. The other completed runs remained in the results. All nine selected runs have matching source records, while the exact cause of the file replacement failure remains uncertain and is described in the saved troubleshooting notes, and the retained failure records support a review of the repair process.",
    "This slide brings together the records that support the results, including a completed run, an individual model request and the successful offline check. The run record identifies the settings and completion status, while each request records the model settings and text use. The saved reasoning example and the table of individual results provide further ways to inspect what happened. The offline check confirms that the prepared data and settings can be loaded with zero model calls, and the repository contains the full records for anyone who wants to examine them after the presentation, using the files listed beneath the displayed records as source references.",
    "The answer checker creates another source of variation because it sometimes rejects a correct number when the response includes a unit or currency symbol. The examples show seventy two degrees compared with seventy two, twelve centimetres compared with twelve, and a dollar amount compared with its number. I identified sixteen formatting related rejections across the repeated evaluations and kept the original scores in the main results. The small question set, its overlap with the earlier test questions and possible changes to the online model also limit broader conclusions. Future work could use more separate questions and validate answer formatting before running the experiment.",
    "The final slide contains the preparation and run commands, together with the public repository address, so the presentation can be recorded entirely from these slides. A reader can install the required packages, check the saved data and run the experiment with a personal DeepSeek key, while the saved results remain available for offline inspection. My main finding is that the program ran under the recorded conditions and achieved ninety percent accuracy with the shortest setting on this subset, using less text than the starting setting of ten. I recommend checking actual search length, resource use and answer formatting when evaluating similar systems, and I thank you for listening to the findings of this project.",
]
DIRECTIONS = [
    "Introduce the project from the title and the three study totals.",
    "Follow the four workflow blocks, then compare the paper and this study.",
    "Point to the three limits, the fixed settings and the displayed code.",
    "Compare the three averages and point to the nine individual run counts.",
    "Compare the token bars, then explain the timing note and the reduction figure.",
    "Read the worked example and point to configured and observed search depth.",
    "Explain each issue, repair and recorded outcome using the three rows.",
    "Point to the run record, request record and saved offline check on this slide.",
    "Compare answer and reference formats, then explain the three study limits.",
    "Point to the commands, repository address and two conclusions before closing.",
]


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def word_count(text):
    return len(re.findall(r"\b[\w-]+\b", text))


def spoken(text):
    return " ".join(re.findall(r"\*\*Say:\*\*\s*(.*?)(?=\n## |\Z)", text, re.S))


def terms(text):
    pattern = r"\b(?:" + "|".join(re.escape(x) for x in sorted(TERMS, key=len, reverse=True)) + r")\b"
    return len(re.findall(pattern, text, re.I))


class Slide:
    def __init__(self, number, section, subtitle="", dark=False):
        self.number, self.shapes, self.dark = number, [], dark
        self.bg = NAVY if dark else BG
        self.rect(0, 0, W, H, self.bg)
        self.rect(64, 46, 32, 5, "76D4B8" if dark else TEAL)
        self.text(110, 35, 900, 30, "FTEC5660 / INDIVIDUAL PROJECT 2 / " + section.upper(), 15,
                  "A6C8C9" if dark else TEAL, True)
        if number != 1:
            self.text(64, 90, 1312, 74, TITLES[number-1], 42, "FFFFFF" if dark else NAVY, True)
            if subtitle:
                self.text(64, 167, 1312, 40, subtitle, 22, "C5D8DF" if dark else MUTED)
        self.line(64, 752, 1376, 752, "36505B" if dark else LINE)
        self.text(64, 766, 1080, 25, "SANG Yuchen  |  1155262204  |  LiTS reproducibility  |  " + TIMES[number-1], 13,
                  "A6C8C9" if dark else MUTED)
        self.text(1250, 761, 126, 35, f"{number:02d} / 10", 20, "A6C8C9" if dark else TEAL, True, align="right")

    def rect(self, x, y, w, h, fill, border=None, rounded=False):
        self.shapes.append(dict(kind="rect", x=x, y=y, w=w, h=h, fill=fill, border=border, rounded=rounded))

    def text(self, x, y, w, h, text, size=24, color=INK, bold=False, align="left", font="Arial"):
        self.shapes.append(dict(kind="text", x=x, y=y, w=w, h=h, text=str(text), size=size,
                                color=color, bold=bold, align=align, font=font))

    def line(self, x1, y1, x2, y2, color=LINE, width=1):
        self.shapes.append(dict(kind="line", x=x1, y=y1, w=x2-x1, h=y2-y1, color=color, width=width))

    def card(self, x, y, w, h, fill="FFFFFF", border=None):
        self.rect(x, y+3, w, h, "E8E8E1" if not self.dark else "0D1B29", rounded=True)
        self.rect(x, y, w, h, fill, border, True)

    def label(self, x, y, text, w=500, color=TEAL):
        self.text(x, y, w, 28, text.upper(), 16, color, True)

    def source(self, text):
        self.text(64, 718, 1312, 25, text, 12, "A6C8C9" if self.dark else MUTED)


def make_slides(results, example, request, check):
    groups = results["groups"]
    slides = []
    s = Slide(1, "The study", dark=True)
    s.text(64, 115, 920, 190, "Testing LiTS\nwith DeepSeek", 72, "FFFFFF", True)
    s.text(68, 312, 860, 78, "How the allowed search steps affect\ncorrect answers and text use", 31, "C6D9DF")
    s.text(68, 419, 920, 44, "SANG Yuchen  |  Student ID 1155262204", 24, "FFFFFF")
    for i, (num, name) in enumerate([("30", "fixed mathematics questions"), ("3", "search limits: 1, 3, 10"), ("9", "completed repeated runs")]):
        x = 64+i*445
        s.card(x, 553, 422, 134, "203B4A")
        s.text(x+24, 572, 100, 75, num, 56, "7BD6B9", True)
        s.text(x+134, 589, 261, 65, name, 23, "FFFFFF")
    for x, y in [(1100, 180), (1010, 300), (1190, 300), (970, 420), (1080, 420), (1250, 420)]:
        if y == 300: s.line(1112, 199, x+12, y+10, "395767", 3)
        if y == 420: s.line(1022 if x < 1120 else 1202, 320, x+12, y+10, "395767", 3)
        s.rect(x, y, 26, 26, "76D4B8", rounded=True)
    s.source("Recorded experiment: 4 November 2026  |  Presentation prepared for a 10 minute recording")
    slides.append(s)

    s = Slide(2, "Project and scope", "The authors' program proposes, checks and selects mathematical solutions.")
    labels = [("01", "Read the question"), ("02", "Propose solutions"), ("03", "Check the options"), ("04", "Select an answer")]
    for i, (num, label) in enumerate(labels):
        x=64+i*337
        s.card(x, 235, 312, 130)
        s.label(x+22, 253, num)
        s.text(x+22, 296, 270, 49, label, 26, NAVY, True)
        if i<3: s.text(x+314, 282, 24, 40, ">", 26, TEAL, True)
    for x, title, score, detail, fill in [(64,"PAPER / TABLE 6","37%","100 questions\nLlama3-8B and the paper's scoring setup","FFFFFF"),
                                            (738,"THIS STUDY / LIMIT 10","85.6%","30 questions, 3 repeats\nDeepSeek and API based scoring",MINT)]:
        s.card(x, 402, 638, 216, fill)
        s.label(x+25, 422, title)
        s.text(x+25, 469, 220, 85, score, 61, NAVY, True)
        s.text(x+264, 473, 350, 105, detail, 23)
    s.text(80, 648, 1275, 42, "Different model, scoring setup and sample size require a qualified comparison.", 25, TEAL, True)
    s.source("Sources: LiTS paper v2, Table 6  |  assignment/experiment_plan.json  |  formal_results.json")
    slides.append(s)

    s = Slide(3, "Test design", "The same questions and shared settings support the comparison.")
    for i, depth in enumerate([1,3,10]):
        x=64+i*261
        s.card(x, 235, 239, 150, MINT if i==0 else "FFFFFF")
        s.label(x+21, 253, "SEARCH LIMIT", 210)
        s.text(x+21, 288, 197, 75, str(depth), 65, NAVY, True)
    s.card(64, 415, 762, 269)
    s.label(88, 435, "HELD FIXED")
    s.text(88, 480, 704, 94, "30 questions in source order\n3 repeats with local seeds 11, 22, 33", 27, NAVY, True)
    s.text(88, 590, 704, 68, "10 search iterations  /  3 alternatives\n2 rollout steps  /  role specific decoding settings", 22)
    s.card(858, 235, 518, 449, NAVY)
    s.label(882, 258, "ENFORCED IN EVERY GROUP", 465, "7BD6B9")
    s.text(882, 314, 465, 125, "max_steps = 1, 3, 10\nforce_terminating_on_\ndepth_limit=True", 23, "FFFFFF", font="Consolas")
    s.text(882, 456, 465, 112, "Model: deepseek-flash\nThinking: disabled\nEndpoint: api.deepseek.com", 23, "D9E8E9")
    s.text(882, 589, 465, 70, "Source: 25e94d8\nData revision: d27dc61", 20, "A6C8C9", font="Consolas")
    s.source("Configuration excerpt, line wrapped for display  |  assignment/experiment_plan.json and assignment/study.py")
    slides.append(s)

    s = Slide(4, "Measured accuracy", "Mean accuracy and sample SD from three repeats on the same 30 questions.")
    for i,g in enumerate(groups):
        x=64+i*445
        s.card(x, 229, 422, 142, MINT if i==0 else "FFFFFF")
        s.label(x+23, 245, f"LIMIT {g['max_steps']}")
        s.text(x+23, 281, 250, 67, f"{100*g['accuracy_mean']:.1f}%", 53, NAVY, True)
        s.text(x+268, 299, 138, 47, f"± {100*g['accuracy_sd']:.1f} pp", 23, MUTED)
    s.card(64, 397, 757, 287)
    s.label(87, 415, "ACCURACY / SAME 30 QUESTIONS")
    for i,g in enumerate(groups):
        y=466+i*58
        s.text(90,y,125,35,f"Limit {g['max_steps']}",23)
        s.rect(217,y+4,490,24,"EDF0ED",rounded=True)
        s.rect(217,y+4,490*g['accuracy_mean'],24, TEAL if i<2 else ORANGE, rounded=True)
        s.text(720,y-1,75,35,f"{100*g['accuracy_mean']:.1f}",21,INK,True,align="right")
    s.card(849,397,527,287)
    s.label(873,415,"ALL NINE CORRECT ANSWER COUNTS")
    for x,t in [(875,"Limit"),(982,"Run 1"),(1103,"Run 2"),(1223,"Run 3")]:
        s.text(x,460,115,33,t,21,MUTED,True)
    for i,depth in enumerate([1,3,10]):
        vals=[r['correct'] for r in results['trials'] if r['max_steps']==depth]
        y=505+i*48
        s.text(875,y,80,36,str(depth),25,TEAL,True)
        for x,v in zip([982,1103,1223],vals):s.text(x,y,110,36,f"{v}/30",25,NAVY,True)
    s.source("Source: formal_trials.csv and formal_results.json  |  Error values describe variation between repeated runs.")
    slides.append(s)

    s = Slide(5,"Resources","Counts include both search and the final answer selection.")
    s.card(64,233,790,451)
    s.label(89,253,"TOKENS PER QUESTION / MEAN")
    for i,g in enumerate(groups):
        y=321+i*103
        s.text(90,y,115,35,f"Limit {g['max_steps']}",24)
        s.rect(218,y+1,449,32,"EDF0ED",rounded=True)
        s.rect(218,y+1,449*g['tokens_per_question_mean']/12000,32,TEAL if i==0 else "7EA5A4",rounded=True)
        s.text(680,y-3,145,47,f"{g['tokens_per_question_mean']:,.0f}",29,NAVY,True,align="right")
        s.text(218,y+42,560,30,f"Sample SD: {g['tokens_per_question_sd']:,.0f}",18,MUTED)
    s.card(884,233,492,198,MINT)
    saving=100*(1-groups[0]['tokens_per_question_mean']/groups[2]['tokens_per_question_mean'])
    s.text(909,253,440,89,f"{saving:.0f}% lower",54,TEAL,True)
    s.text(909,350,440,55,"token use at limit 1 versus limit 10",23)
    s.card(884,458,492,226)
    s.label(909,477,"RECORDED SECONDS / QUESTION")
    s.text(909,521,440,40,"14.6     16.9     17.5",31,NAVY,True)
    s.text(909,571,440,83,"Limits 1, 3, 10\nTiming is descriptive: one retry ran alone; the first batch used 9 processes.",20)
    s.source("Source: formal_results.json  |  4,425 formal model calls  |  Token counts represent consumption before price calculation.")
    slides.append(s)

    s = Slide(6,"Interpretation","A single generated action may contain a complete calculation.")
    s.card(64,234,756,450)
    s.label(89,253,"SAVED QUESTION 0 / LIMIT 1, RUN 1")
    s.text(89,301,700,81,"How many positive whole numbers\ndivide 196?",30,NAVY,True)
    s.rect(89,405,702,151,MINT,rounded=True)
    s.text(115,428,650,55,"196 = 2² × 7²",40,TEAL,True)
    s.text(115,489,650,45,"(2 + 1) × (2 + 1) = 9",33,NAVY,True)
    s.text(89,589,701,66,"Several mathematical operations\nwere completed inside one saved action.",25)
    s.card(850,234,526,450)
    s.label(875,253,"CONFIGURED AND OBSERVED DEPTH")
    for x,t in [(875,"Limit"),(1037,"Mean*"),(1190,"Deepest")]:s.text(x,308,155,36,t,22,MUTED,True)
    for i,g in enumerate(groups):
        y=366+i*70
        for x,t in [(875,str(g['max_steps'])),(1037,f"{g['mean_max_observed_depth_mean']:.2f}"),(1190,str(g['max_observed_depth']))]:
            s.text(x,y,155,46,t,32,TEAL if x==1190 else NAVY,True)
    s.text(875,583,470,85,"*Mean maximum depth per question.\nThe limit also controls when the final answer instruction is supplied.",20,MUTED)
    s.source("Source: evidence/steps1_seed11/full_trees.jsonl, full_tree_0.json  |  Calculation reformatted from the saved action.")
    slides.append(s)

    s = Slide(7,"Troubleshooting","Compatibility changes were shared across all formal groups.")
    for x,t in [(88,"OBSERVED ISSUE"),(546,"CHANGE"),(1007,"RECORDED OUTCOME")]:s.label(x,229,t)
    rows=[("DeepSeek request options","Adjusted thinking and tool settings","9 selected formal runs completed with the shared API path."),
          ("Special character write failed","Used UTF-8 when saving text","The initial test and retained error record are documented."),
          ("Completion file replacement failed","Retained the attempt and repeated the entire test once","The other 8 completed runs were retained; the retry used identical source.")]
    for i,(a,b,c) in enumerate(rows):
        y=276+i*123
        s.card(64,y,1312,105)
        s.rect(64,y,8,105,TEAL if i<2 else ORANGE,rounded=True)
        s.text(88,y+22,406,73,a,25,NAVY,True)
        s.text(546,y+22,406,73,b,24)
        s.text(1007,y+17,342,83,c,21,MUTED)
    s.text(88,673,1250,35,"Nine selected runs have matching source hashes; the file replacement failure has an uncertain cause.",23,TEAL,True)
    s.source("Source: assignment/DEBUG_DIARY.md, lits/lm/openai_chat.py, evidence/index.json and common_source_hashes.json")
    slides.append(s)

    s = Slide(8,"Embedded evidence","Selected recorded fields are displayed here; the complete files remain in the repository.")
    cards=[(64,"COMPLETED RUN",[("Status","complete"),("Model","deepseek-flash"),("Search limit","1"),("Question count","30"),("Local seed","11")]),
           (509,"SAMPLE REQUEST",[("Request status",request['status']),("Input tokens",str(request['usage']['prompt_tokens'])),("Output tokens",str(request['usage']['completion_tokens'])),("Output limit","512"),("top_p / temperature","0.95 / 0.000001")]),
           (954,"SAVED OFFLINE CHECK",[("Status",check['status']),("Python",check['python']),("Dataset rows",str(check['dataset_rows'])),("Formal rows",str(check['formal_rows'])),("Model calls",str(check['real_api_calls']))])]
    for x,title,entries in cards:
        s.card(x,235,422,386,MINT if x==954 else "FFFFFF")
        s.label(x+22,255,title,385)
        for i,(key,value) in enumerate(entries):
            y=310+i*57
            s.text(x+22,y,380,24,key,17,MUTED)
            s.text(x+22,y+22,380,32,value,25,NAVY,True)
    s.rect(64,648,1312,45,NAVY,rounded=True)
    s.text(84,656,1270,30,"Full records: settings, request use, evaluated answers, saved reasoning and excluded attempts",23,"FFFFFF")
    s.source("Sources: steps1_seed11/run_manifest.json and api_calls.jsonl, call 1  |  Offline preflight: saved on 12 November 2026")
    slides.append(s)

    s = Slide(9,"Scoring and limits","16 formatting related rejections were recorded across the 270 question evaluations.")
    s.card(64,234,757,450)
    s.label(89,254,"ANSWER FORMAT / ORIGINAL CHECKER")
    for x,t in [(89,"Saved answer"),(388,"Reference"),(613,"Outcome")]:s.text(x,308,220,35,t,21,MUTED,True)
    for i,(pred,ref) in enumerate([("72°","72"),("12 cm","12"),("$78","78")]):
        y=365+i*73
        s.text(89,y,276,43,pred,31,NAVY,True)
        s.text(388,y,180,43,ref,31,NAVY,True)
        s.text(613,y+6,180,37,"Rejected",24,ORANGE,True)
    s.rect(89,598,704,58,MINT,rounded=True)
    s.text(109,612,665,36,"Primary scores retain the original checker results.",23,TEAL,True)
    s.card(850,234,526,450)
    s.label(875,254,"CONDITIONS THAT LIMIT CONCLUSIONS")
    for i,(title,detail) in enumerate([("30 distinct questions","An ordered subset with 5 pilot questions overlapping."),
                                      ("Online model variation","The model service and model based scoring can vary."),
                                      ("Different paper conditions","Model, scoring setup and sample size differ.")]):
        y=308+i*113
        s.text(875,y,470,37,title,27,NAVY,True)
        s.text(875,y+42,470,62,detail,22,MUTED)
    s.source("Source: formal_trials.csv, format_audit.json and experiment_plan.json  |  Diagnostic examples; primary scores remain unchanged.")
    slides.append(s)

    s = Slide(10,"Reproduce and conclude", "The presentation contains the demonstration material for recording.",dark=True)
    s.card(64,235,785,374,"203B4A")
    s.label(88,254,"COMMANDS / IN AN ACTIVE PYTHON 3.12 ENVIRONMENT",745,"7BD6B9")
    cmds=[("01  Install the required packages","python -m pip install -r\n    assignment/requirements-api.lock.txt"),
          ("02  Prepare the fixed data","python -m assignment.prepare_data"),
          ("03  Check the data and settings","python -m assignment.study preflight"),
          ("04  Repeat the selected test","python -m assignment.study run --phase formal\n    --max-steps 1 --seed 11")]
    for i,(label,cmd) in enumerate(cmds):
        y=[295,383,452,521][i]
        s.text(88,y,735,26,label,18,"A6C8C9",True)
        s.text(88,y+29,735,57,cmd,20,"FFFFFF",font="Consolas")
    s.card(881,235,495,374,"203B4A")
    s.label(905,254,"FINDINGS ON THIS SUBSET",450,"7BD6B9")
    s.text(905,307,446,100,"90.0% accuracy\nat limit 1",34,"FFFFFF",True)
    s.text(905,416,446,75,"26% lower token use\nversus limit 10",31,"7BD6B9",True)
    s.text(905,529,446,58,"Measure search length, resource\nuse and answer formatting.",22,"C5D8DF")
    s.text(64,632,1310,37,"github.com/programharu-creator/FTEC5660-Individual-Project-2-Reproducibility",21,"FFFFFF",True)
    s.text(64,676,1310,32,"Commands are line wrapped for display. Set your key in the ignored .env file; repeat limits 1, 3, 10 and seeds 11, 22, 33.",17,"C5D8DF")
    s.source("Full steps and offline evidence restoration: repository README  |  Recording link remains pending until recorded and shared.")
    slides.append(s)
    for s in slides:
        s.notes = NARRATION[s.number-1]
        s.direction = DIRECTIONS[s.number-1]
    return slides


def write_script():
    lines=["# English recording script for a ten minute presentation", "", "Author: eula", "",
           "**FTEC5660 Individual Project 2: Reproducibility**", "", "**Presenter: SANG Yuchen | 1155262204**", "",
           "The spoken text is approximately two thirds of the previous version. Allow about ten minutes at a comfortable pace of roughly 110 to 120 words per minute, including pauses for pointing to the slide content. The assignment maximum is 15 minutes.", "",
           "## Recording setup", "",
           "Open FTEC5660_Presentation.pptx in slide show mode, or use the matching PDF in full screen. All examples, results, configuration excerpts, saved checks and commands needed for the presentation are embedded in these ten slides. Keep the script in presenter view or on a second screen and share the slide show through Zoom. Advance through the slides according to the timing table, using the directions to point to information already visible on the current slide.", "",
           "## Slide plan", "", "| Time | Slide | Display within the current slide |", "|---|---|---|"]
    for i in range(10):lines.append(f"| {TIMES[i]} | {i+1} | {DIRECTIONS[i]} |")
    for i in range(10):lines.extend(["",f"## {TIMES[i]}: Slide {i+1}, {TITLES[i]}","","**Screen:** "+DIRECTIONS[i],"","**Say:**","",NARRATION[i]])
    lines.extend(["","## After recording","","Review the sound, readability and duration, then share the Zoom recording through an accessible link and update VIDEO_LINK.md with its address and actual duration. Submit the report, public repository URL and recording link through the course submission channel before the stated deadline.",""])
    text="\n".join(lines)
    assert not re.search(r'[\u2013\u2014\u201c\u201d"]',text)
    assert not re.search(r"\b(?:not|rather than|instead of|but)\b", " ".join(NARRATION), re.I)
    (OUT/"RECORDING_SCRIPT_EN.md").write_text(text,encoding="utf-8")
    return text


def main():
    CACHE.mkdir(parents=True,exist_ok=True)
    results=read("assignment/deliverables/formal_results.json")
    check_path = CACHE/'preflight.json'
    check=json.loads(check_path.read_text(encoding='utf-8')) if check_path.exists() else read('assignment/deliverables/presentation_evidence.json')['preflight_check']
    evidence=ROOT/"assignment/evidence/steps1_seed11"
    example=json.loads((evidence/"full_trees.jsonl").read_text(encoding="utf-8").splitlines()[0])
    request=json.loads((evidence/"api_calls.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert example['filename']=='full_tree_0.json' and '196' in example['content']['action']
    assert check['status']=='passed' and check['real_api_calls']==0
    evidence_summary={'author':AUTHOR,'preflight_check':check,'preflight_date':'2026-11-12',
                      'request_record':request,'question_example':example['filename'],
                      'question_source':'assignment/evidence/steps1_seed11/full_trees.jsonl'}
    (OUT/'presentation_evidence.json').write_text(json.dumps(evidence_summary,indent=2)+'\n',encoding='utf-8')
    baseline_record=json.loads((Path(__file__).parent/'narration_baseline.json').read_text(encoding='utf-8'))
    baseline=baseline_record['spoken_text']
    text=write_script()
    before,after=baseline,spoken(text)
    audit={'author':AUTHOR,'previous_spoken_words':word_count(before),'current_spoken_words':word_count(after),
           'length_ratio':round(word_count(after)/word_count(before),4),
           'previous_glossary_mentions':terms(before),'current_glossary_mentions':terms(after),
           'glossary_reduction':round(1-terms(after)/terms(before),4),'glossary':TERMS,
           'glossary_note':'Same fixed list, longer phrases matched first; this is a reproducible terminology indicator.',
           'slides':10,'target_seconds':600,'external_window_switches':0,'author_metadata':AUTHOR}
    assert .63<=audit['length_ratio']<=.70,audit
    assert audit['glossary_reduction']>=1/3,audit
    slides=make_slides(results,example,request,check)
    for s in slides:
        for sh in s.shapes:
            if sh['kind']=='text':
                assert not re.search(r'[\u2013\u2014\u201c\u201d"]',sh['text']),sh
    specification={'author':AUTHOR,'width':W,'height':H,'slides':[{'title':TITLES[s.number-1], 'notes':s.notes,
                   'direction':s.direction,'time':TIMES[s.number-1],'shapes':s.shapes} for s in slides]}
    (CACHE/'presentation_spec.json').write_text(json.dumps(specification,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (OUT/'presentation_revision_check.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k not in ['glossary','glossary_note']},indent=2))
    if '--render' in sys.argv:
        subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
                        str(ROOT/'assignment/reporting/render_presentation.ps1')],check=True)
        finalize()
    else:
        render_pdf(slides)


def render_pdf(slides):
    """Rebuild the PDF using the existing report dependencies on any platform."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.utils import simpleSplit
    fonts={}
    for name,file,fallback in [('normal','arial.ttf','Helvetica'),('bold','arialbd.ttf','Helvetica-Bold'),('mono','consola.ttf','Courier')]:
        source=Path('C:/Windows/Fonts')/file
        if source.exists():
            registered='Presentation'+name;pdfmetrics.registerFont(TTFont(registered,str(source)));fonts[name]=registered
        else:fonts[name]=fallback
    c=canvas.Canvas(str(OUT/'FTEC5660_Presentation.pdf'),pagesize=(960,540))
    c.setAuthor(AUTHOR);c.setTitle('FTEC5660 Reproducibility: ten minute presentation')
    for slide in slides:
        c.saveState();c.scale(2/3,2/3)
        for sh in slide.shapes:
            x,y,w,h=sh['x'],sh['y'],sh['w'],sh['h']
            if sh['kind']=='rect':
                c.setFillColor(HexColor('#'+sh['fill']))
                stroke=bool(sh['border'])
                if stroke:c.setStrokeColor(HexColor('#'+sh['border']))
                if sh['rounded']:c.roundRect(x,H-y-h,w,h,min(w,h)*.09,stroke=int(stroke),fill=1)
                else:c.rect(x,H-y-h,w,h,stroke=int(stroke),fill=1)
            elif sh['kind']=='line':
                c.setStrokeColor(HexColor('#'+sh['color']));c.setLineWidth(sh['width']);c.line(x,H-y,x+w,H-y-h)
            elif sh['kind']=='text':
                font=fonts['mono' if sh['font']=='Consolas' else 'bold' if sh['bold'] else 'normal']
                c.setFont(font,sh['size']);c.setFillColor(HexColor('#'+sh['color']))
                offset=0
                for paragraph in sh['text'].split('\n'):
                    for line in simpleSplit(paragraph,font,sh['size'],w):
                        baseline=H-y-sh['size']-offset
                        if sh['align']=='right':c.drawRightString(x+w,baseline,line)
                        elif sh['align']=='center':c.drawCentredString(x+w/2,baseline,line)
                        else:c.drawString(x,baseline,line)
                        offset+=sh['size']*1.12
        c.restoreState();c.showPage()
    c.save()


def finalize():
    import pymupdf
    from PIL import Image, ImageDraw
    pptx=OUT/'FTEC5660_Presentation.pptx'
    with zipfile.ZipFile(pptx) as archive:
        entries={info.filename:(info,archive.read(info.filename)) for info in archive.infolist()}
    core=entries['docProps/core.xml'][1].decode('utf-8')
    for key,value in [('dc:creator',AUTHOR),('cp:lastModifiedBy',AUTHOR),
                      ('dc:title','FTEC5660 Reproducibility: ten minute presentation')]:
        pattern=r'<'+re.escape(key)+r'(?:\s[^>]*)?>.*?</'+re.escape(key)+r'>'
        replacement='<'+key+'>'+value+'</'+key+'>'
        if re.search(pattern,core,re.S):core=re.sub(pattern,lambda match:replacement,core,flags=re.S)
        else:core=core.replace('</cp:coreProperties>',replacement+'</cp:coreProperties>')
    # Preserve original namespace declarations, including prefixes in xsi:type values.
    entries['docProps/core.xml']=(entries['docProps/core.xml'][0],core.encode('utf-8'))
    temp=pptx.with_suffix('.tmp.pptx')
    with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as archive:
        for info,data in entries.values():archive.writestr(info,data)
    temp.replace(pptx)
    pdf=OUT/'FTEC5660_Presentation.pdf';doc=pymupdf.open(pdf)
    metadata=doc.metadata;metadata.update(author=AUTHOR,title='FTEC5660 Reproducibility: ten minute presentation')
    doc.set_metadata(metadata)
    temp_pdf=pdf.with_suffix('.tmp.pdf');doc.save(temp_pdf);doc.close();temp_pdf.replace(pdf)
    doc=pymupdf.open(pdf)
    sheet=Image.new('RGB',(1280,1850),'#d8dedb')
    for i,page in enumerate(doc):
        pix=page.get_pixmap(matrix=pymupdf.Matrix(1,1),alpha=False)
        pix.save(str(CACHE/f'slide_{i+1:02d}.png'))
        image=Image.open(CACHE/f'slide_{i+1:02d}.png');image.thumbnail((620,349))
        x=10+(i%2)*640;y=10+(i//2)*368
        sheet.paste(image,(x,y))
    sheet.save(CACHE/'contact_sheet.png')
    print('Editable PowerPoint, matching PDF and slide previews saved; author: eula.')


if __name__=='__main__':main()
