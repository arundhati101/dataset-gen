from pypdf import PdfReader
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_PDF_DIR = os.path.join(BASE_DIR, "data", "raw")
OUT_DIR = os.path.join(BASE_DIR, "data", "extracted")

os.makedirs(OUT_DIR, exist_ok=True)

for pdf_file in os.listdir(RAW_PDF_DIR):
    if not pdf_file.lower().endswith(".pdf"):
        continue

    pdf_path = os.path.join(RAW_PDF_DIR, pdf_file)
    reader = PdfReader(pdf_path)

    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"

    out_path = os.path.join(
        OUT_DIR, pdf_file.replace(".pdf", ".txt")
    )

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Extracted: {pdf_file}")
