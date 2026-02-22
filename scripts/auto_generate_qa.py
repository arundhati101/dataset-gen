import os
import re
import json
import hashlib
from pypdf import PdfReader


# ================= PATHS =================
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
OUT_FILE = os.path.join(PROJECT_ROOT, "data", "legal_qa.json")

os.makedirs(os.path.join(PROJECT_ROOT, "data"), exist_ok=True)


# ================= HASH =================
def make_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ================= PDF EXTRACT =================
def extract_pdf(path):
    reader = PdfReader(path)
    text = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text.append(t)
    return "\n".join(text)


# ================= GLOBAL CLEAN =================
def clean_global(text):

    text = text.replace("\r", "\n")

    # Remove standalone page numbers
    text = re.sub(r"\n\s*\d+\s*\n", "\n", text)

    # Remove chapter headings
    text = re.sub(r"\nCHAPTER\s+[IVXLC]+\b.*?\n", "\n", text, flags=re.I)

    # Remove bracketed amendment insertions like 1[23A...
    text = re.sub(r"\d+\[", "", text)

    # Remove amendment notes fully
    text = re.sub(r"Ins\. by Act.*?(?=\.)\.", "", text, flags=re.I)
    text = re.sub(r"Subs\. by Act.*?(?=\.)\.", "", text, flags=re.I)

    # Remove star markers like 2***
    text = re.sub(r"\d+\*+", "", text)

    # 🔥 Remove stray footnote numbers between words
    # Example: "date 3 as" → "date as"
    text = re.sub(r"(?<=\w)\s+\d+\s+(?=\w)", " ", text)

    # 🔥 Remove superscript-style footnote numbers after words
    # Example: "date3" → "date"
    text = re.sub(r"(?<=\w)\d+(?=\s)", "", text)

    # Collapse spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize blank lines
    text = re.sub(r"\n{2,}", "\n", text)

    return text.strip()

# ================= HEADER NORMALIZATION =================
def normalize_section_headers(text):
    """
    Converts:
        2 Definitions
        2—Definitions
        2 - Definitions
        2. Definitions
    into:
        2. Definitions
    """

    text = re.sub(
        r"^\s*(\d+[A-Z]?(?:-[A-Z])?)\s*(?:\.|—|-|–)?\s+(?=[A-Z\(])",
        r"\1. ",
        text,
        flags=re.MULTILINE,
    )

    return text


# ================= SPLIT SECTIONS =================
def split_sections(text):
    """
    Strict section splitting.
    Stops at:
        - Next numbered section
        - ALL CAPS headings
        - Definition-style patterns like (a) "term"
    """

    section_pattern = re.compile(
        r"^\s*(\d+[A-Z]?(?:-[A-Z])?)\.\s+",
        re.MULTILINE,
    )

    matches = list(section_pattern.finditer(text))
    sections = []

    for i, match in enumerate(matches):

        sec_num = match.group(1)
        start = match.end()

        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(text)

        body = text[start:end]

        # Stop at ALL CAPS heading
        caps_heading = re.search(r"\n[A-Z][A-Z\s]{4,}\n", body)
        if caps_heading:
            body = body[:caps_heading.start()]

        # 🔥 Stop at definition clauses like (a) “term”
        definition_start = re.search(r"\([a-z]\)\s*[\"“]", body)
        if definition_start:
            body = body[:definition_start.start()]

        # 🔥 Stop at inserted section like 23A.
        inserted_section = re.search(r"\n\s*\d+[A-Z]?\.\s", body)
        if inserted_section:
            body = body[:inserted_section.start()]

        body = body.strip()

        if len(body.split()) < 15:
            continue

        sections.append((sec_num, body))

    return sections


# ================= CLEAN SECTION BODY =================
def clean_section_body(text):

    # Fix broken words (info rmation → information)
    text = re.sub(r"(\w)\s+(\w)", r"\1 \2", text)

    # Remove leftover amendment markers
    text = re.sub(r"\[\s*.*?\s*\]", "", text)

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ================= VALID SECTION FILTER =================
def valid_section(text):

    if len(text.split()) < 20:
        return False

    if not re.search(r"\b(shall|may|means|includes|provides|liable|entitled|extends|applies)\b", text):
        return False

    return True


# ================= MAIN =================
def main():

    dataset = []
    hashes = set()

    for file in os.listdir(RAW_DIR):

        if not file.lower().endswith(".pdf"):
            continue

        law = file.replace(".pdf", "")
        path = os.path.join(RAW_DIR, file)

        print(f"\n📘 Processing {law}")

        raw = extract_pdf(path)
        raw = clean_global(raw)
        raw = normalize_section_headers(raw)

        sections = split_sections(raw)
        print(f"   Sections detected: {len(sections)}")

        added = 0

        for sec, body in sections:

            body = clean_section_body(body)

            if not valid_section(body):
                continue

            label = f"Section {sec}"

            question = f"What does {label} of the {law} state?"
            answer = body  # pure statutory language

            h = make_hash(law + label + body)

            if h in hashes:
                continue

            dataset.append(
                {
                    "id": f"{law}-{label}",
                    "law": law,
                    "section": label,
                    "question": question,
                    "context": body,
                    "answer": answer,
                    "hash": h,
                }
            )

            hashes.add(h)
            added += 1

        print(f"   QA pairs added: {added}")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print("\n===================================")
    print(f"FINAL DATASET SIZE: {len(dataset)}")
    print("===================================")


if __name__ == "__main__":
    main()