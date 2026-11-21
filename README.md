# Prompt Engineering: Meeting Notes → Action Items

A measured, step-by-step prompt engineering experiment. An LLM turns messy meeting notes into clean tables of **task, owner and deadline**. Each step changes exactly one thing in the prompt, and every run is scored by a script against a hand-made answer key.

All data is fictional (a film crew making *Neon Monsoon* and a music team releasing the album *Paper Kites*). Model under test: **Claude Haiku 5.5** (medium effort), with a new chat for every run.

## Why this is harder than it looks

The 10 meeting notes contain **36 real action items** plus deliberate traps:

- decisions and status updates that are *not* tasks
- a cancelled task, a task already done, and an optional "might do" idea
- a reassigned task, a task with two owners, and two tasks in one sentence
- 5 tasks that nobody owns yet
- messy lowercase notes and a Hinglish note ("Friday tak DCP export kar dena", "kal tak bhej do")

## Results

| Step | One change | Found | Fully correct | Extra rows | "No deadline" spellings | Untranslated Hindi | Table per note |
|---|---|---|---|---|---|---|---|
| 1 | Baseline: *"Extract the action items … as a table."* | 36/36 | 36/36 | 1 | 3 | 0 | no |
| 2 | Only "firmly agreed" tasks; exclude decisions / cancelled / done / optional | **30/36** | 30/36 | 0 | 2 | 0 | no |
| 3 | Reworded scope: offers count, unowned tasks → `Unassigned` | 36/36 | 36/36 | 0 | 3 | 0 | no |
| 4 | Deadline "exactly as stated", `None` if missing | 36/36 | **35/36** | 0 | 1 | **3** | no |
| 5 | Deadline rule rewritten: English, keep "after X" conditions | 36/36 | 36/36 | 0 | 1 | 0 | no |
| 6 | Fixed format: one table per note, `Task \| Owner \| Deadline`, nothing else | 36/36 | 36/36 | 0 | 1 | 0 | **yes** |
| 7 | Final prompt on **3 unseen notes** | 9/9 | 9/9 | 0 | 1 | 0 | yes |
| 8 | Same unseen test re-run (stability) | 9/9 | 9/9 | 0 | 1 | 0 | yes |

## Key findings

- **Strict wording backfires.** Asking for "firmly agreed" tasks removed the optional idea as intended, but it also dropped all 5 unowned tasks and a clear *"I can get the photos to Zoya by Saturday"*, which the model called "an offer rather than an agreed task". Recall fell from 36 to 30.
- **"Exactly as stated" is taken literally.** The model copied Hindi deadlines word for word ("kal tak") and decided "after the score is done" wasn't a deadline. Rules worked when they said what *to* do and gave a concrete value ("translate Hindi", "write exactly `None`").
- **Finding the tasks was the easy part.** A one-line prompt found all 36 items. The real prompting work was in the edges: what counts as a task, consistent missing values, and a fixed, script-readable format.
- **The model invents small details.** It added a recipient ("send guest list *to Tara*") that the notes never mention.
- **The final prompt generalises.** It scored 9/9 on new notes, twice, and translated Hindi it was never told about ("aaj raat" → tonight, "parso" → day after tomorrow).

Full write-up: [report.pdf](report.pdf).

## Repository layout

```
prompt_log.csv              Every run: model, prompt, output summary, problem seen, next change, why
report.pdf                  2-page write-up
artifact/
  final_prompt.txt          The final prompt (step 6)
  meeting_notes.txt         The 10 fictional meeting notes
  answer_key.csv            Hand-labelled key: 36 items
  prompts/stepN.txt         Exact prompt sent at each step
  outputs/stepN.md          Unedited model reply at each step
  outputs/stepN_score.txt   Scorer output at each step
  unseen_notes.txt          3 new notes for the generalisation test (+ unseen_answer_key.csv)
  results_summary.csv       All metrics in one table
  score.py                  Scoring script
```

## Reproduce a score

Requires Python 3 and no extra packages.

```bash
cd artifact
python score.py outputs/step2.md
python score.py outputs/unseen_test.md unseen_answer_key.csv
```

The scorer reads markdown, tab-separated or CSV tables. It matches each key item by task keywords and owner, then checks the deadline. It also reports extra rows, text outside the tables, inconsistent missing values and untranslated Hindi.

## Limitations

- Steps 1–6 were each run once; only the final prompt was re-run for stability.
- The final prompt hard-codes the number of notes ("10 headings").
- Date style still varies ("By Friday" vs "Monday", "3 Jan" vs "3 January").
- Matching is keyword-based, so every output was also checked by eye.

## AI use

Prompts were run on Claude Haiku 5.5. Claude Code helped draft the fictional notes and answer keys, write the scoring script, and lay out the report.
