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


# ================= CLEAN GLOBAL TEXT =================
def clean_global(text):

    # Normalize line endings
    text = text.replace("\r", "\n")

    # Remove standalone page numbers
    text = re.sub(r"\n\s*\d+\s*\n", "\n", text)

    # Remove chapter headings
    text = re.sub(r"\nCHAPTER\s+[IVXLC]+\b.*?\n", "\n", text, flags=re.I)

    # Remove schedules fully
    text = re.sub(
        r"\nSCHEDULE\s+[IVXLC]+\b.*?(?=\n\d+[A-Z]?(?:-[A-Z])?\.)",
        "\n",
        text,
        flags=re.S | re.I,
    )

    # Remove amendment bracket notes
    text = re.sub(r"\[(Ins\.|Subs\.|Vide).*?\]", "", text, flags=re.I)

    # Collapse multiple spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize excessive blank lines
    text = re.sub(r"\n{2,}", "\n", text)

    return text.strip()


# ================= FIX BROKEN SECTION HEADERS =================
def normalize_section_headers(text):
    """
    Converts:
        2 Definitions
        2—Definitions
        2 - Definitions
    into:
        2. Definitions
    """

    text = re.sub(
        r"^\s*(\d+[A-Z]?(?:-[A-Z])?)\s*(?:[—\-–])?\s+(?=[A-Z])",
        r"\1. ",
        text,
        flags=re.MULTILINE,
    )

    return text


# ================= SPLIT SECTIONS =================
def split_sections(text):
    """
    Detects:
        1.
        2.
        33A.
        14-I.
    Anchored at line start only.
    """

    section_pattern = re.compile(
        r"""
        ^\s*
        (?P<num>\d+[A-Z]?(?:-[A-Z])?)
        \.\s+
        (?=[A-Z\(])
        """,
        re.MULTILINE | re.VERBOSE,
    )

    matches = list(section_pattern.finditer(text))
    sections = []

    for i, match in enumerate(matches):

        sec_num = match.group("num")
        start = match.end()

        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(text)

        body = text[start:end].strip()

        if len(body.split()) < 10:
            continue

        sections.append((sec_num, body))

    return sections


# ================= CLEAN SECTION BODY =================
def clean_section_body(text):

    # Remove leftover amendment stars
    text = re.sub(r"\*\*+.*", "", text)

    # Remove numeric garbage sequences
    text = re.sub(r"(?:\d{2,},\s*){4,}\d+", "", text)

    # Fix line break joins inside sentences
    text = re.sub(r"\n(?=[a-z])", " ", text)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ================= VALID SECTION FILTER =================
def valid_section(text):

    if len(text.split()) < 20:
        return False

    if not re.search(
        r"\b(shall|may|means|includes|provides|liable|entitled|extends|applies)\b",
        text,
        re.I,
    ):
        return False

    return True


# ================= MAIN =================
def main():

    dataset = []
    hashes = set()
    seen_sections = set()
    section_index = {}

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

            # Merge duplicates inside same Act
            if (law, label) in seen_sections:
                print(f"   ⚠️ duplicate {label}, merging")
                idx = section_index[(law, label)]

                existing = dataset[idx]
                new_context = existing["context"] + " " + body

                existing["context"] = new_context
                existing["answer"] = (
                    f"{label} of the {law} provides that {new_context}"
                )

                new_hash = make_hash(law + label + new_context)
                hashes.discard(existing["hash"])
                existing["hash"] = new_hash
                hashes.add(new_hash)

                continue

            question = f"What does {label} of the {law} state?"
            answer = f"{label} of the {law} provides that {body}"

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

            section_index[(law, label)] = len(dataset) - 1
            seen_sections.add((law, label))
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