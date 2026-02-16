import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

IN_DIR = os.path.join(BASE_DIR, "data", "cleaned")
OUT_DIR = os.path.join(BASE_DIR, "data", "clauses")

os.makedirs(OUT_DIR, exist_ok=True)

# Pattern matches:
# 1.
# 12.
# 12A.
# 12B.
# 12(1)
# etc.
SECTION_PATTERN = re.compile(r'\n\s*\d+[A-Za-z]?\.\s')

for file in os.listdir(IN_DIR):
    if not file.endswith(".txt"):
        continue

    in_path = os.path.join(IN_DIR, file)
    with open(in_path, encoding="utf-8") as f:
        text = f.read()

    # Ensure numbers start on new line
    text = re.sub(r'(\d+\.)', r'\n\1', text)

    # Split into sections
    parts = re.split(SECTION_PATTERN, text)

    clauses = []
    for p in parts:
        cleaned = p.strip()
        if len(cleaned.split()) > 40:
            clauses.append(cleaned)

    out_path = os.path.join(OUT_DIR, file)
    with open(out_path, "w", encoding="utf-8") as f:
        for c in clauses:
            f.write(c + "\n\n")

    print(f"{file}: generated {len(clauses)} clauses")
