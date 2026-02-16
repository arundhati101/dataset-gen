import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

IN_DIR = os.path.join(BASE_DIR, "data", "extracted")
OUT_DIR = os.path.join(BASE_DIR, "data", "cleaned")

os.makedirs(OUT_DIR, exist_ok=True)

for file in os.listdir(IN_DIR):
    if not file.endswith(".txt"):
        continue

    name = file.replace(".txt", "")
    in_path = os.path.join(IN_DIR, file)
    out_path = os.path.join(OUT_DIR, file)

    with open(in_path, "r", encoding="utf-8") as f:
        text = f.read()

    # remove page numbers & headers junk
    text = re.sub(r"\n\s*\d+\s*\n", "\n", text)

    # remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    # normalize line breaks after sections
    text = re.sub(r"(\d+\.)", r"\n\1", text)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text.strip())

    print(f"✅ {name} cleaned → {out_path}")
