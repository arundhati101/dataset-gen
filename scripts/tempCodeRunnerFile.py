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
    """Compute a SHA256 digest of *text*.

    This is used to detect duplicates when assembling the dataset:
    laws with identical wording for the same section will hash to the
    same value.
    """
    # encode the incoming string as UTF-8 bytes for hashing
    encoded = text.encode("utf-8")
    # compute SHA256 digest and return its hexadecimal representation
    digest = hashlib.sha256(encoded)
    return digest.hexdigest()


# ================= PDF EXTRACT =================

def extract_pdf(path):
    """Read all textual content from a PDF file at *path*.

    The `pypdf.PdfReader` returns each page separately; we collect the
    non‑empty text blocks and join them with a newline so that
    subsequent regex operations treat the document as a single string.
    """
    # open the PDF; PdfReader lazily reads pages
    reader = PdfReader(path)
    # accumulate text from each page in this list
    text = []
    for page in reader.pages:
        # attempt to extract text; may return None
        t = page.extract_text()
        if t:
            # only keep pages that yielded text
            text.append(t)
    # join the page strings using newline separators
    return "\n".join(text)


# ================= GLOBAL CLEAN =================

def clean_global(text):
    """Perform broad document‑level cleanup on *text* extracted from a PDF.

    This function normalizes line endings, strips page headers/footers,
    removes amendment markers and stray footnote numerals, collapses
    excessive whitespace, and generally prepares the string for
    reliable section splitting.
    """

    # convert DOS CRs to unix newlines so our regexes are simpler
    text = text.replace("\r", "\n")

    # Remove standalone page numbers
    text = re.sub(r"\n\s*\d+\s*\n", "\n", text)

    # Remove chapter headings that might confuse section detection
    text = re.sub(r"\nCHAPTER\s+[IVXLC]+\b.*?\n", "\n", text, flags=re.I)

    # Remove bracketed amendment insertions like 1[23A...
    text = re.sub(r"\d+\[", "", text)

    # Remove amendment notes fully (they aren't part of actual prose)
    text = re.sub(r"Ins\. by Act.*?(?=\.)\.", "", text, flags=re.I)
    text = re.sub(r"Subs\. by Act.*?(?=\.)\.", "", text, flags=re.I)

    # Remove star markers like 2*** which indicate versioning
    text = re.sub(r"\d+\*+", "", text)

    # 🔥 Remove stray footnote numbers between words
    # Example: "date 3 as" → "date as"
    text = re.sub(r"(?<=\w)\s+\d+\s+(?=\w)", " ", text)

    # 🔥 Remove superscript-style footnote numbers after words
    # Example: "date3" → "date"
    text = re.sub(r"(?<=\w)\d+(?=\s)", "", text)

    # Collapse sequences of spaces/tabs to a single space
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize multiple blank lines into one
    text = re.sub(r"\n{2,}", "\n", text)

    return text.strip()

# ================= HEADER NORMALIZATION =================

def normalize_section_headers(text):
    """Standardize various numeric header formats to a canonical form.

    Many statutes will render section numbers with dashes, em‑dashes,
    or missing punctuation.  We convert them all to "<number>. <Title>"
    so that the section splitter can match reliably.
    """

    # perform regex replacement once across all lines
    text = re.sub(
        r"^\s*(\d+[A-Z]?(?:-[A-Z])?)\s*(?:\.|—|-|–)?\s+(?=[A-Z\(])",
        # capture the number and ensure a trailing period + space
        r"\1. ",
        text,
        flags=re.MULTILINE,
    )

    return text


# ================= SPLIT SECTIONS =================

def split_sections(text):
    """Break cleaned document *text* into a list of (number, body) tuples.

    The logic looks for numbered headings and additionally truncates the
    body if it encounters all‑caps headers, definition clauses, or
    embedded section numbers; this helps avoid pulling large unrelated
    text into a single section.
    """

    # compile the regex that identifies section headers with trailing dot
    section_pattern = re.compile(
        r"^\s*(\d+[A-Z]?(?:-[A-Z])?)\.\s+",
        re.MULTILINE,
    )

    # find all occurrences of the pattern
    matches = list(section_pattern.finditer(text))
    sections = []

    for i, match in enumerate(matches):
        # extract the numeric label for the section
        sec_num = match.group(1)
        # determine where the content of this section begins
        start = match.end()

        # determine where this section ends (start of next, or end of text)
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

        # trim whitespace around the extracted body text
        body = body.strip()

        # skip any bodies that are ridiculously short/noisy
        if len(body.split()) < 15:
            continue

        # store the tuple for later processing
        sections.append((sec_num, body))

    return sections


# ================= CLEAN SECTION BODY =================

def clean_section_body(text):
    """Tidy up the interior of a section after it has been isolated."""

    # Fix broken words where a space was introduced in the middle
    text = re.sub(r"(\w)\s+(\w)", r"\1 \2", text)

    # Remove leftover amendment markers enclosed in brackets
    text = re.sub(r"\[\s*.*?\s*\]", "", text)

    # Collapse any sequence of whitespace characters into one space
    text = re.sub(r"\s+", " ", text)

    # strip leading/trailing whitespace and return
    return text.strip()


# ================= VALID SECTION FILTER =================

def valid_section(text):
    """Determine whether *text* is substantial enough to form a QA pair.

    Rejects very tiny sections and those lacking any of a set of
    indicative legal verbs/terms.
    """

    # reject anything shorter than twenty words
    if len(text.split()) < 20:
        return False

    # require presence of at least one signal verb/term
    if not re.search(r"\b(shall|may|means|includes|provides|liable|entitled|extends|applies)\b", text):
        return False

    return True


# ================= MAIN =================
def main():
    """Entry point: iterate over raw PDFs, extract sections, and
    build a list of QA pairs.

    The dataset and hashes structures accumulate results across all
    files.  At the end we serialize the list to OUT_FILE as JSON.
    """

    dataset = []         # list of section dictionaries
    hashes = set()       # to prevent duplicates by content hash

    for file in os.listdir(RAW_DIR):
        # iterate over every entry in the raw directory

        if not file.lower().endswith(".pdf"):
            # ignore non-PDF files such as directories or text files
            continue

        law = file.replace(".pdf", "")      # human-readable identifier
        path = os.path.join(RAW_DIR, file)

        # print progress so user knows which file is being handled
        print(f"\n📘 Processing {law}")

        raw = extract_pdf(path)
        raw = clean_global(raw)
        raw = normalize_section_headers(raw)

        sections = split_sections(raw)
        print(f"   Sections detected: {len(sections)}")

        added = 0

        for sec, body in sections:

            # further clean the section text before evaluation
            body = clean_section_body(body)

            # skip anything that doesn't meet our quality checks
            if not valid_section(body):
                continue

            label = f"Section {sec}"

            # form the QA prompt and capture the answer verbatim
            question = f"What does {label} of the {law} state?"
            answer = body

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

        # report how many sections from this law were incorporated
        print(f"   QA pairs added: {added}")

    # dump the final dataset to disk in a human-readable format
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print("\n===================================")
    print(f"FINAL DATASET SIZE: {len(dataset)}")
    print("===================================")


if __name__ == "__main__":
    main()