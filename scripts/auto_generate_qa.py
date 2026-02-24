import os
import re
import json
import hashlib
from pypdf import PdfReader


# ================= PATHS =================
# Build absolute paths relative to this file's location so the script works
# regardless of the working directory it's launched from.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")       # Folder containing input PDF files
OUT_FILE = os.path.join(PROJECT_ROOT, "data", "legal_qa.json")  # Output QA dataset

# Create the data/ folder if it doesn't exist yet (idempotent — safe to call repeatedly)
os.makedirs(os.path.join(PROJECT_ROOT, "data"), exist_ok=True)


# ================= HASH =================
def make_hash(text):
    # Generate a SHA-256 fingerprint for a piece of text.
    # Used later to deduplicate entries — if the same law + section + body
    # is encountered twice (e.g., duplicate PDFs), the hash will match and it
    # will be skipped.
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ================= PDF EXTRACT =================
def extract_pdf(path):
    # Open the PDF and iterate over every page, collecting non-empty text blocks.
    reader = PdfReader(path)
    text = []
    for page in reader.pages:
        t = page.extract_text()
        if t:                     # Skip blank/image-only pages that return None or ""
            text.append(t)
    # Join all pages with newlines to preserve paragraph boundaries across pages
    return "\n".join(text)


# ================= GLOBAL CLEAN =================
def clean_global(text):
    # First pass of cleaning applied to the entire raw PDF text before sectioning.
    # Handles noise that spans the whole document (page numbers, footnotes, etc.)

    # Normalize Windows-style line endings to Unix-style
    text = text.replace("\r", "\n")

    # Remove standalone page numbers — lines that contain only a digit (e.g., "\n 42 \n")
    text = re.sub(r"\n\s*\d+\s*\n", "\n", text)

    # Remove chapter headings like "CHAPTER IV" which add no legal content
    text = re.sub(r"\nCHAPTER\s+[IVXLC]+\b.*?\n", "\n", text, flags=re.I)

    # Remove bracketed amendment insertions like "1[23A" — artifacts from
    # Indian law PDFs where amendment numbers appear inline with brackets
    text = re.sub(r"\d+\[", "", text)

    # Remove full amendment note sentences (these cite the amending Act, not the law itself)
    text = re.sub(r"Ins\. by Act.*?(?=\.)\.", "", text, flags=re.I)
    text = re.sub(r"Subs\. by Act.*?(?=\.)\.", "", text, flags=re.I)

    # Remove star markers like "2***" used in Indian statute books to denote omissions
    text = re.sub(r"\d+\*+", "", text)

    # 🔥 Remove stray footnote numbers between words (PDF extraction artifact)
    # Example: "date 3 as" → "date as"
    # Lookahead/lookbehind ensure the digit is surrounded by word characters with spaces
    text = re.sub(r"(?<=\w)\s+\d+\s+(?=\w)", " ", text)

    # 🔥 Remove superscript-style footnote numbers directly after words
    # Example: "date3 something" → "date something"
    # The digit is attached to the preceding word but followed by whitespace
    text = re.sub(r"(?<=\w)\d+(?=\s)", "", text)

    # Collapse multiple spaces/tabs into a single space (but preserve newlines)
    text = re.sub(r"[ \t]+", " ", text)

    # Collapse multiple consecutive blank lines into one
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

    Why: Indian statutes use inconsistent separator styles between the section
    number and title. Normalizing to "N. Title" format lets split_sections()
    rely on a single regex pattern.
    """

    text = re.sub(
        r"^\s*(\d+[A-Z]?(?:-[A-Z])?)\s*(?:\.|—|-|–)?\s+(?=[A-Z\(])",
        # Group 1 captures the section number (e.g., "2", "23A", "2-A")
        # The separator (., —, -, –) is optional and consumed but not kept
        # Lookahead (?=[A-Z\(]) ensures the title starts with a capital or open paren
        r"\1. ",
        text,
        flags=re.MULTILINE,  # ^ matches start of each line, not just the string
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

    Returns a list of (section_number, body_text) tuples.
    """

    # Match lines that start a new numbered section, e.g. "2. " or "23A. " or "2-A. "
    section_pattern = re.compile(
        r"^\s*(\d+[A-Z]?(?:-[A-Z])?)\.\s+",
        re.MULTILINE,
    )

    matches = list(section_pattern.finditer(text))
    sections = []

    for i, match in enumerate(matches):

        sec_num = match.group(1)   # The section number string, e.g. "23A"
        start = match.end()        # Body starts right after the "N. " header

        # Body ends at the start of the next section (or end of document for the last)
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(text)

        body = text[start:end]

        # Stop at ALL CAPS heading — these are schedule/part titles, not section content
        # e.g. "\nFIRST SCHEDULE\n" would pollute the section body
        caps_heading = re.search(r"\n[A-Z][A-Z\s]{4,}\n", body)
        if caps_heading:
            body = body[:caps_heading.start()]

        # 🔥 Stop at definition clauses like (a) "term" — these belong to a
        # separate definitions section and their structure breaks QA generation
        definition_start = re.search(r"\([a-z]\)\s*[\""]", body)
        if definition_start:
            body = body[:definition_start.start()]

        # 🔥 Stop at an inserted sub-section like "23A." that wasn't caught by
        # the top-level pattern (happens when amendments insert sections mid-text)
        inserted_section = re.search(r"\n\s*\d+[A-Z]?\.\s", body)
        if inserted_section:
            body = body[:inserted_section.start()]

        body = body.strip()

        # Discard very short bodies — fewer than 15 words can't form a meaningful QA pair
        if len(body.split()) < 15:
            continue

        sections.append((sec_num, body))

    return sections


# ================= CLEAN SECTION BODY =================
def clean_section_body(text):
    # Second-pass cleaning applied per section after splitting.

    # Fix broken words caused by PDF column layout or hyphenation artifacts
    # e.g. "info rmation" → "information" (the regex joins a word char gap)
    text = re.sub(r"(\w)\s+(\w)", r"\1 \2", text)

    # Remove any leftover square-bracket amendment markers like "[omitted]"
    text = re.sub(r"\[\s*.*?\s*\]", "", text)

    # Collapse all remaining whitespace (tabs, multiple spaces) to single space
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ================= VALID SECTION FILTER =================
def valid_section(text):
    # Quality gate — skip sections that are too short or lack substantive legal language.

    # Minimum word count: anything under 20 words is likely a heading or stub
    if len(text.split()) < 20:
        return False

    # Must contain at least one operative legal keyword.
    # Sections without these are probably transitional provisions, schedules,
    # or formatting artifacts rather than substantive law.
    if not re.search(r"\b(shall|may|means|includes|provides|liable|entitled|extends|applies)\b", text):
        return False

    return True


# ================= MAIN =================
def main():

    dataset = []      # Accumulates all QA entries across all PDFs
    hashes = set()    # Tracks seen content hashes to prevent duplicate entries

    for file in os.listdir(RAW_DIR):

        if not file.lower().endswith(".pdf"):
            continue   # Skip non-PDF files (e.g. .DS_Store, README.md)

        # Use the filename (without extension) as the law name, e.g. "Indian_Contract_Act"
        law = file.replace(".pdf", "")
        path = os.path.join(RAW_DIR, file)

        print(f"\n📘 Processing {law}")

        # Step 1: Extract raw text from every PDF page
        raw = extract_pdf(path)
        # Step 2: Apply document-wide noise removal
        raw = clean_global(raw)
        # Step 3: Normalize inconsistent section header formats
        raw = normalize_section_headers(raw)

        # Step 4: Split into (section_number, body) pairs
        sections = split_sections(raw)
        print(f"   Sections detected: {len(sections)}")

        added = 0

        for sec, body in sections:

            # Step 5: Per-section text cleaning
            body = clean_section_body(body)

            # Step 6: Quality gate — skip short or non-substantive sections
            if not valid_section(body):
                continue

            label = f"Section {sec}"   # Human-readable label, e.g. "Section 23A"

            # Generate a natural-language question from the section metadata.
            # This becomes the "question" field in the RAG knowledge base.
            question = f"What does {label} of the {law} state?"
            answer = body  # The raw statutory text is the authoritative answer

            # Build a deduplication hash from law name + section label + body text.
            # This ensures the same section from the same law is never added twice,
            # even if the PDF appears more than once in RAW_DIR.
            h = make_hash(law + label + body)

            if h in hashes:
                continue   # Skip duplicate

            dataset.append(
                {
                    "id": f"{law}-{label}",        # Unique identifier for this QA entry
                    "law": law,                     # Source statute name
                    "section": label,               # Section label (e.g. "Section 23A")
                    "question": question,           # Auto-generated retrieval question
                    "context": body,                # Statutory text used as RAG context
                    "answer": answer,               # Same text — the ground-truth answer
                    "hash": h,                      # Content hash for deduplication
                }
            )

            hashes.add(h)
            added += 1

        print(f"   QA pairs added: {added}")

    # Write the complete dataset to a single JSON file for downstream indexing
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)   # ensure_ascii=False preserves Unicode (Hindi, etc.)

    print("\n===================================")
    print(f"FINAL DATASET SIZE: {len(dataset)}")
    print("===================================")


if __name__ == "__main__":
    main()