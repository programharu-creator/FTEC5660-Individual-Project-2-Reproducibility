# English recording script for a ten minute presentation

Author: eula

**FTEC5660 Individual Project 2: Reproducibility**

**Presenter: SANG Yuchen | 1155262204**

The spoken text is approximately two thirds of the previous version. Allow about ten minutes at a comfortable pace of roughly 110 to 120 words per minute, including pauses for pointing to the slide content. The assignment maximum is 15 minutes.

## Recording setup

Open FTEC5660_Presentation.pptx in slide show mode, or use the matching PDF in full screen. All examples, results, configuration excerpts, saved checks and commands needed for the presentation are embedded in these ten slides. Keep the script in presenter view or on a second screen and share the slide show through Zoom. Advance through the slides according to the timing table, using the directions to point to information already visible on the current slide.

## Slide plan

| Time | Slide | Display within the current slide |
|---|---|---|
| 00:00-00:40 | 1 | Introduce the project from the title and the three study totals. |
| 00:40-01:35 | 2 | Follow the four workflow blocks, then compare the paper and this study. |
| 01:35-02:35 | 3 | Point to the three limits, the fixed settings and the displayed code. |
| 02:35-03:40 | 4 | Compare the three averages and point to the nine individual run counts. |
| 03:40-04:35 | 5 | Compare the token bars, then explain the timing note and the reduction figure. |
| 04:35-05:30 | 6 | Read the worked example and point to configured and observed search depth. |
| 05:30-06:25 | 7 | Explain each issue, repair and recorded outcome using the three rows. |
| 06:25-07:30 | 8 | Point to the run record, request record and saved offline check on this slide. |
| 07:30-08:40 | 9 | Compare answer and reference formats, then explain the three study limits. |
| 08:40-10:00 | 10 | Point to the commands, repository address and two conclusions before closing. |

## 00:00-00:40: Slide 1, Testing LiTS with DeepSeek

**Screen:** Introduce the project from the title and the three study totals.

**Say:**

Hello, my name is SANG Yuchen, and this presentation explains my FTEC5660 reproducibility project, which uses LiTS with DeepSeek to solve a small set of mathematics questions. I studied how the allowed number of search steps affects correct answers and resource use, using thirty questions and repeating each setting three times. The results show that a shorter setting achieved strong scores with lower token use, and the following slides contain the setup, measured results and saved records, with all nine completed runs included in the final comparison.

## 00:40-01:35: Slide 2, What I reproduced

**Screen:** Follow the four workflow blocks, then compare the paper and this study.

**Say:**

LiTS works through several stages, proposing possible solutions, checking their quality and choosing an answer from the available results. This process makes it suitable for studying how additional search affects performance. The paper reports thirty seven percent accuracy on one hundred mathematics questions, while my version uses DeepSeek and thirty questions with a different scoring setup. Those differences require care when interpreting the numbers, so my controlled comparison focuses on the three search limits within the same setup. The diagram and comparison cards show the workflow I reproduced and the conditions that define this smaller study, and the original code remains responsible for producing and checking the answers.

## 01:35-02:35: Slide 3, One setting changes across three groups

**Screen:** Point to the three limits, the fixed settings and the displayed code.

**Say:**

The three groups allow one, three or ten search steps, with ten serving as the starting setting for comparison. Each group receives the same thirty questions in the same order, and the program repeats the test three times while keeping the other settings fixed. The code shown here makes the search limit apply in every group, which matters because a setting needs to affect actual program behavior before its results can be interpreted. I also recorded the source version, data version and model settings so that another reader can identify the materials used for these runs, including the five preparation questions that also appear in the final set.

## 02:35-03:40: Slide 4, Accuracy across all nine runs

**Screen:** Compare the three averages and point to the nine individual run counts.

**Say:**

The results table contains all nine completed runs, with every score calculated from thirty planned questions and missing answers counted as incorrect. The average accuracy is ninety percent at limits one and three, compared with eighty five point six percent at limit ten. The values beside each average show how much the scores varied across the three runs, and the right hand table shows the individual correct answer counts. These results suggest limited benefit from allowing more steps on this small question set, while a larger evaluation would help establish how well this pattern applies to other questions, and every completed run contributes equally to the reported averages.

## 03:40-04:35: Slide 5, Text use rises with the search limit

**Screen:** Compare the token bars, then explain the timing note and the reduction figure.

**Say:**

The model service counts text use in tokens, which are pieces of text processed when reading questions and producing answers. The recorded average rises from about eight thousand five hundred per question at limit one to about eleven thousand four hundred at limit ten, giving the shorter setting roughly twenty six percent lower use. Recorded time also increases, although the runs used different levels of simultaneous activity because one test was repeated alone after a file saving failure. I therefore use time as a descriptive result and treat the text counts as the clearer resource comparison, with searching and final answer selection both included in the saved counts.

## 04:35-05:30: Slide 6, One search step can include a full calculation

**Screen:** Read the worked example and point to configured and observed search depth.

**Say:**

The example on this slide helps explain why a short search can work well. One question asks how many positive whole numbers divide one hundred and ninety six, and the saved response completes the calculation inside a single generated action. A search step can therefore contain several mathematical operations. The recorded depth also shows that the group allowing ten steps reached a maximum of four, because many answers finished earlier. Changing the limit also changes when the program asks for a final answer, so the measured effect includes that instruction as well as the permitted search length, with the displayed calculation preserving the outcome of the saved response.

## 05:30-06:25: Slide 7, Repairs that made the experiment run

**Screen:** Explain each issue, repair and recorded outcome using the three rows.

**Say:**

Several practical repairs helped the program run successfully on this computer. I prepared a suitable Python environment, adjusted the settings sent to DeepSeek, and changed how the program saves special characters on Windows. A later attempt failed while replacing a completion file, so I kept that incomplete attempt and repeated the entire affected test once with the same source and settings. The other completed runs remained in the results. All nine selected runs have matching source records, while the exact cause of the file replacement failure remains uncertain and is described in the saved troubleshooting notes, and the retained failure records support a review of the repair process.

## 06:25-07:30: Slide 8, Saved records show how the experiment ran

**Screen:** Point to the run record, request record and saved offline check on this slide.

**Say:**

This slide brings together the records that support the results, including a completed run, an individual model request and the successful offline check. The run record identifies the settings and completion status, while each request records the model settings and text use. The saved reasoning example and the table of individual results provide further ways to inspect what happened. The offline check confirms that the prepared data and settings can be loaded with zero model calls, and the repository contains the full records for anyone who wants to examine them after the presentation, using the files listed beneath the displayed records as source references.

## 07:30-08:40: Slide 9, Answer formatting affects the score

**Screen:** Compare answer and reference formats, then explain the three study limits.

**Say:**

The answer checker creates another source of variation because it sometimes rejects a correct number when the response includes a unit or currency symbol. The examples show seventy two degrees compared with seventy two, twelve centimetres compared with twelve, and a dollar amount compared with its number. I identified sixteen formatting related rejections across the repeated evaluations and kept the original scores in the main results. The small question set, its overlap with the earlier test questions and possible changes to the online model also limit broader conclusions. Future work could use more separate questions and validate answer formatting before running the experiment.

## 08:40-10:00: Slide 10, Reproduce the test and use the evidence

**Screen:** Point to the commands, repository address and two conclusions before closing.

**Say:**

The final slide contains the preparation and run commands, together with the public repository address, so the presentation can be recorded entirely from these slides. A reader can install the required packages, check the saved data and run the experiment with a personal DeepSeek key, while the saved results remain available for offline inspection. My main finding is that the program ran under the recorded conditions and achieved ninety percent accuracy with the shortest setting on this subset, using less text than the starting setting of ten. I recommend checking actual search length, resource use and answer formatting when evaluating similar systems, and I thank you for listening to the findings of this project.

## After recording

Review the sound, readability and duration, then share the Zoom recording through an accessible link and update VIDEO_LINK.md with its address and actual duration. Submit the report, public repository URL and recording link through the course submission channel before the stated deadline.
