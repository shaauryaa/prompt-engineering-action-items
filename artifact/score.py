"""Score a model's action-item tables against answer_key.csv.

Usage:  python score.py outputs/step1.md [answer_key.csv]

Reads every markdown table row in the output file. A key item counts as
FOUND when a row's task text contains one of its keywords and the row's
owner matches. It counts as FULLY CORRECT when the deadline also matches.
Rows that match no key item are reported as EXTRA (non-tasks or invented).
"""
import csv
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
NONE_WORDS = ["none", "n/a", "not stated", "not specified", "not mentioned",
              "no deadline", "tbd", "tba", "unspecified", "not given", "null",
              "not set", "to be decided", "not fixed", "no date"]
UNASSIGNED_WORDS = ["unassigned", "none", "not assigned", "not specified", "tbd",
                    "unspecified", "someone", "anyone", "team", "no owner",
                    "not stated", "not mentioned", "open", "null", "n/a"]


def clean(s):
    return re.sub(r"[*_`]", "", s).strip().lower()


def is_blankish(cell, words):
    c = clean(cell).strip(" .-–—")
    return c == "" or any(w in c for w in words)


def find_col(header, names):
    for i, h in enumerate(header):
        if any(n in h for n in names):
            return i
    return None


def split_cells(s):
    """Split a table line (markdown pipes, tabs or CSV). Return None if not a table line."""
    if s.startswith("|"):
        return [clean(c) for c in s.strip("|").split("|")]
    if "\t" in s:
        return [clean(c) for c in s.split("\t")]
    if s.count(",") >= 2 and not s.endswith("."):
        cells = next(csv.reader([s]))
        if all(len(c) <= 60 for c in cells):  # prose sentences are not CSV rows
            return [clean(c) for c in cells]
    return None


def parse_rows(text):
    """Return (rows, other_lines). rows = (task, owner, deadline, raw_line)."""
    rows, other, header, note = [], [], None, None
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"^[#*\s]*note\s*(\d+)", s.lower())
        if m:
            note = m.group(1)
        cells = split_cells(s)
        if cells is None:
            header = None
            is_heading = s.startswith("#") or re.fullmatch(r"\**note\s*\d+.*", s.lower())
            if s and not is_heading and not s.startswith("```"):
                other.append(s)
            continue
        if all(re.fullmatch(r":?-{2,}:?", c) or c == "" for c in cells):
            continue  # separator row
        if header is None:
            header = cells
            continue
        t = find_col(header, ["task", "action", "item", "what"])
        o = find_col(header, ["owner", "assign", "responsible", "who", "person"])
        d = find_col(header, ["deadline", "due", "date", "when", "timeline", "by"])
        get = lambda i: cells[i] if i is not None and i < len(cells) else ""
        rows.append((get(t) if t is not None else " ".join(cells), get(o), get(d), s, note))
    return rows, other


def owner_ok(expected, cell):
    if expected == "Unassigned":
        return is_blankish(cell, UNASSIGNED_WORDS)
    names = [n.strip().lower() for n in re.split(r"&|and", expected)]
    return all(n in cell for n in names)


def deadline_ok(accept, cell):
    opts = [a.strip().lower() for a in accept.split(";")]
    if "none" in opts and is_blankish(cell, NONE_WORDS):
        return True
    return any(a != "none" and a in cell for a in opts)


def main():
    out_file = Path(sys.argv[1])
    rows, other = parse_rows(out_file.read_text(encoding="utf-8"))
    key_file = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "answer_key.csv"
    key = list(csv.DictReader(open(key_file, encoding="utf-8")))
    used = set()
    found = correct = 0
    wrong_note = []
    missed, wrong_deadline = [], []

    for item in key:
        kws = [k.lower() for k in item["task_keywords"].split(";")]
        match = None
        for i, (task, owner, dl, _, _n) in enumerate(rows):
            if i in used:
                continue
            if any(k in task for k in kws) and owner_ok(item["owner"], owner):
                match = i
                break
        optional = item.get("optional") == "yes"
        if match is None:
            if not optional:
                missed.append(item)
            continue
        used.add(match)
        if optional:  # e.g. a task the model reasonably split in two
            continue
        if rows[match][4] is not None and rows[match][4] != item["note"]:
            wrong_note.append((item, rows[match][4]))
        found += 1
        if deadline_ok(item["deadline_accept"], rows[match][2]):
            correct += 1
        else:
            wrong_deadline.append((item, rows[match][2]))

    extras = [rows[i][3] for i in range(len(rows)) if i not in used]
    n = sum(1 for k in key if k.get("optional") != "yes")
    hindi = [r[2] for r in rows if re.search(r"\b(tak|kal|baad|mein|parson|parso|aaj|raat)\b", r[2])]
    # Format consistency: how many different spellings for "no deadline" / "no owner"
    none_keys = [k for k in key if k["deadline_accept"].upper().startswith("NONE")]
    none_spellings = sorted({rows[i][2] for i in used for k in none_keys
                             if k["task_keywords"].split(";")[0] in rows[i][0]
                             and is_blankish(rows[i][2], NONE_WORDS)})
    owner_spellings = sorted({r[1] for r in rows if is_blankish(r[1], UNASSIGNED_WORDS)})
    print(f"File: {out_file.name}")
    print(f"Table rows parsed:            {len(rows)}")
    print(f"Items found (task + owner):   {found}/{n}")
    print(f"Fully correct (+ deadline):   {correct}/{n}")
    print(f"Missed or wrong owner:        {len(missed)}")
    print(f"Wrong deadline:               {len(wrong_deadline)}")
    print(f"Extra rows (non-tasks etc.):  {len(extras)}")
    print(f"Text lines outside table:     {len(other)}")
    print(f"'No deadline' spellings:      {len(none_spellings)} {none_spellings}")
    print(f"'No owner' spellings:         {len(owner_spellings)} {owner_spellings}")
    has_notes = any(r[4] for r in rows)
    print(f"Tables split by NOTE heading: {'yes' if has_notes else 'no'}"
          + (f" ({len(wrong_note)} tasks under the wrong note)" if has_notes else ""))
    print(f"Untranslated Hindi deadlines: {len(hindi)} {hindi}")
    if missed:
        print("\nMISSED / WRONG OWNER:")
        for m in missed:
            print(f"  {m['id']:5} {m['task']}  (owner: {m['owner']})")
    if wrong_deadline:
        print("\nWRONG DEADLINE:")
        for m, got in wrong_deadline:
            print(f"  {m['id']:5} {m['task']}  expected '{m['deadline']}', got '{got}'")
    if extras:
        print("\nEXTRA ROWS:")
        for e in extras:
            print(f"  {e}")


if __name__ == "__main__":
    main()
