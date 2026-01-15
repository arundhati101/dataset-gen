import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

IN_DIR = os.path.join(BASE_DIR, "data", "cleaned")
OUT_DIR = os.path.join(BASE_DIR, "data", "clauses")

os.makedirs(OUT_DIR, exist_ok=True)

for file in os.listdir(IN_DIR):
    if not file.endswith(".txt"):
        continue

    with open(os.path.join(IN_DIR, file), encoding="utf-8") as f:
        text = f.read()

    clauses = []
    current = []

    for line in text.split("\n"):
        if line.strip().startswith("Section"):
            if current:
                clauses.append(" ".join(current))
                current = []
        current.append(line.strip())

    if current:
        clauses.append(" ".join(current))

    out_path = os.path.join(OUT_DIR, file)
    with open(out_path, "w", encoding="utf-8") as f:
        for c in clauses:
            if len(c.split()) > 40:
                f.write(c.strip() + "\n\n")

    print(f"Split clauses: {file}")
