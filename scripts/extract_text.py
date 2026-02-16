import os
from pypdf import PdfReader

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
OUT_DIR = os.path.join(BASE_DIR, "data", "extracted")

os.makedirs(OUT_DIR, exist_ok=True)

for file in os.listdir(RAW_DIR):
    if not file.lower().endswith(".pdf"):
        continue

    name = file.replace(".pdf", "")
    pdf_path = os.path.join(RAW_DIR, file)
    out_path = os.path.join(OUT_DIR, f"{name}.txt")

    reader = PdfReader(pdf_path)
    text = ""

    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"✅ {name} extracted → {out_path}")
