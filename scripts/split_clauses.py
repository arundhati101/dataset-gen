import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

IN_DIR = os.path.join(BASE_DIR, "data", "cleaned")
OUT_DIR = os.path.join(BASE_DIR, "data", "clauses")

os.makedirs(OUT_DIR, exist_ok=True)


def split_into_clauses(text):

    # split at section numbers
    parts = re.split(r"(?=\b\d+\.\s[A-Z])", text)

    clauses = []

    for p in parts:
        # split at subsections like (1) or (a)
        sub = re.split(r"(?=\(\d+\)|\([a-z]\))", p)
        clauses.extend(sub)

    # remove small junk
    clauses = [c.strip() for c in clauses if len(c.strip()) > 120]

    return clauses


for file in os.listdir(IN_DIR):
    if not file.endswith(".txt"):
        continue

    name = file.replace(".txt", "")
    in_path = os.path.join(IN_DIR, file)
    out_path = os.path.join(OUT_DIR, file)

    with open(in_path, "r", encoding="utf-8") as f:
        text = f.read()

    clauses = split_into_clauses(text)

    with open(out_path, "w", encoding="utf-8") as f:
        for c in clauses:
            f.write(c + "\n\n")

    print(f"✅ {name} split → {len(clauses)} clauses")
