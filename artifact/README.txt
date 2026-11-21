B06 Action items - artifact folder (domain: movies and music, all names and titles fictional)

final_prompt.txt        The final prompt (step 6), including the 10 meeting notes.
meeting_notes.txt       The 10 fictional meeting notes used in every step.
answer_key.csv          My hand-made key: 36 action items (task, owner, deadline).
results_summary.csv     One line per run with all measured numbers.
prompts/stepN.txt       The exact full prompt sent in each step of prompt_log.csv.
outputs/stepN.md        The model's unedited reply for each step.
outputs/stepN_score.txt Scorer result for each step (counts of missed items etc.).
unseen_notes.txt        3 new notes used to test the final prompt (unseen_answer_key.csv = 9 items).
outputs/unseen_test.*   Reply and score for that test (log row 7).
outputs/unseen_test_run2.*  Same test re-run in a new chat for stability (log row 8).
score.py                Scoring script (Python 3, no extra packages).

Re-check any score:
  python score.py outputs/step3.md
  python score.py outputs/unseen_test.md unseen_answer_key.csv
