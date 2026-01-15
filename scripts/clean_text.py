import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

IN_DIR = os.path.join(BASE_DIR, "data", "extracted")
OUT_DIR = os.path.join(BASE_DIR, "data", "cleaned")

os.makedirs(OUT_DIR, exist_ok=True)

for file in os.listdir(IN_DIR):
    if not file.endswith(".txt"):
        continue

    with open(os.path.join(IN_DIR, file), encoding="utf-8") as f:
        text = f.read()

    text = re.sub(r"STATE AMENDMENTS.*?(Section|\Z)", r"\1", text, flags=re.S)
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\n{2,}", "\n", text)

    out_path = os.path.join(OUT_DIR, file)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text.strip())

    print(f"Cleaned: {file}")
