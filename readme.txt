📚 DATASET-GEN
Legal QA Dataset Generator

Build a structured Question–Answer dataset from law PDFs automatically.

🚀 Overview

DATASET-GEN extracts section-wise legal text from raw law PDFs and generates a structured QA dataset.

Reads PDFs from data/raw/

Extracts and cleans section text

Generates templated questions

Outputs a single dataset file:
data/legal_qa.json

Generated question format:

What does Section X of the <Law Name> state?

Each record includes:

Cleaned section text

Generated question

Answer (currently identical to context)

Stable SHA-256 hash for deduplication

📂 Project Structure
dataset-gen/
├── requirements.txt
├── README.md
├── data/
│   ├── legal_qa.json        # Generated QA dataset
│   └── raw/                 # Source law PDFs
└── scripts/
    ├── auto_generate_qa.py  # Main generator
    ├── check_duplicates.py  # Conflict checker
    └── remove_duplicates.py # Hard deduplication utility
⚙️ What the Generator Does

File: scripts/auto_generate_qa.py

1️⃣ Reads PDFs

Uses pypdf.PdfReader to extract text from each PDF inside data/raw/.

2️⃣ Global Cleanup

Normalize newlines and spacing

Remove standalone page numbers

Remove chapter headings

Remove amendment markers

Remove footnote-number artifacts

3️⃣ Normalize Section Headers

Standardizes section headers into a consistent format:

<number>. <Title>
4️⃣ Section Splitting

Splits text into sections using numbered header detection.

5️⃣ Noise Trimming

Stops section extraction when:

ALL-CAPS headings appear

Definition clauses start ((a) "term")

Inserted sections appear (e.g., 23A.)

6️⃣ Quality Filtering

Rejects sections that:

Have fewer than 20 words

Do not contain legal signal words such as:

shall, may, means, includes, provides,
liable, entitled, extends, applies
7️⃣ QA Generation

For each valid section:

Builds a templated question

Uses cleaned section text as answer

Computes SHA-256 hash from:

law + section label + cleaned body
8️⃣ Writes Output

Exports full dataset to:

data/legal_qa.json
🧾 Output Schema

Each dataset entry:

{
  "id": "Aadhaar Act, 2016-Section 3",
  "law": "Aadhaar Act, 2016",
  "section": "Section 3",
  "question": "What does Section 3 of the Aadhaar Act, 2016 state?",
  "context": "<cleaned section text>",
  "answer": "<same as context>",
  "hash": "<sha256 hex digest>"
}
🔎 Duplicate & Conflict Handling
1️⃣ Conflict Checker

File: scripts/check_duplicates.py

Detects:

Same normalized question

Different answer texts

Outputs:

Each conflicting question

All unique answer variants

Summary counts

2️⃣ Hard Deduplication

File: scripts/remove_duplicates.py

Removes:

Exact duplicate hashes

Duplicate question + answer pairs

Rewrites:

data/legal_qa.json
🛠 Setup
Windows (PowerShell)

From project root:

1. Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
2. Install dependencies
pip install -r requirements.txt
▶️ Usage
Generate dataset
python scripts/auto_generate_qa.py
Check conflicts
python scripts/check_duplicates.py
Remove duplicates
python scripts/remove_duplicates.py
🧠 Recommended Workflow

Add/update PDFs in data/raw/

Run generator

Run conflict checker

Run duplicate remover (if needed)

Manually inspect problematic sections

⚠️ Notes

Only keep PDF files inside data/raw/

Law name is derived from PDF filename

OCR-heavy PDFs may affect section quality

Regeneration overwrites data/legal_qa.json

Conflict script helps detect ambiguous entries

📌 Current Status

Dataset file: data/legal_qa.json

Raw law corpus: data/raw/

Generator + validation scripts operational