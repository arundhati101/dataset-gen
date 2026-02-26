DATASET-GEN (Legal QA Dataset Generator)
======================================

Overview
--------
This project builds a legal Question-Answer dataset from law PDFs.
It reads files from `data/raw/`, extracts section-wise legal text, and writes a
single JSON dataset to `data/legal_qa.json`.

The generated questions follow this template:
  "What does Section X of the <Law Name> state?"

Each record stores both context and answer text (currently identical), plus a
stable hash used for duplicate filtering.


Project Structure
-----------------
dataset-gen/
├─ requirements.txt
├─ readme.txt
├─ data/
│  ├─ legal_qa.json           # generated QA dataset
│  └─ raw/                    # source law PDFs
└─ scripts/
   ├─ auto_generate_qa.py     # main generator
   └─ check_duplicates.py     # conflict checker


What the Generator Does
-----------------------
File: `scripts/auto_generate_qa.py`

1) Reads every PDF in `data/raw/` using `pypdf.PdfReader`.
2) Applies global cleanup:
   - normalizes newlines/spaces
   - removes standalone page numbers
   - removes chapter headings and amendment markers
   - removes many footnote-number artifacts
3) Normalizes section headers to a consistent pattern like:
   "<number>. <title>"
4) Splits text into sections using numbered header detection.
5) Trims section body when noisy boundaries are detected (e.g., all-caps
   headings, definition clause starts, inserted section markers).
6) Filters out low-quality sections:
   - fewer than 20 words, or
   - missing legal signal terms such as: shall, may, means, includes,
     provides, liable, entitled, extends, applies
7) Builds QA rows and computes SHA-256 hash from:
   law + section label + cleaned body
8) Writes the final dataset to `data/legal_qa.json`.


Output Schema
-------------
Each item in `data/legal_qa.json` has:

- id       : "<Law Name>-Section <number>"
- law      : law name derived from PDF filename
- section  : section label like "Section 3A"
- question : generated natural-language question
- context  : cleaned section text
- answer   : same text as context (for QA training)
- hash     : SHA-256 hex digest for de-duplication


Duplicate/Conflict Checking
---------------------------
File: `scripts/check_duplicates.py`

This script checks for question collisions where the SAME normalized question
maps to DIFFERENT answer texts.

It prints:
- each conflicting question
- all unique answer variants for that question
- summary counts at the end

Use this after generation to detect ambiguous/inconsistent entries.


Setup (Windows PowerShell)
--------------------------
From project root:

1) Create and activate virtual environment
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

2) Install dependencies
   pip install -r requirements.txt


Run
---
Generate dataset:
   python scripts/auto_generate_qa.py

Check conflicts:
   python scripts/check_duplicates.py


Notes and Practical Tips
------------------------
- Keep only PDF files in `data/raw/` for clean runs.
- Law name in output comes from the PDF filename (without `.pdf`).
- If a PDF has unusual formatting/OCR noise, section splitting quality may vary.
- Re-running generation overwrites `data/legal_qa.json`.
- Conflict output from `check_duplicates.py` is useful for manual review and
  post-processing.


Recommended Workflow
--------------------
1) Add/update PDFs in `data/raw/`
2) Run generator (`auto_generate_qa.py`)
3) Run conflict checker (`check_duplicates.py`)
4) Manually inspect and clean problematic entries if needed


Current Status
--------------
- Dataset file present: `data/legal_qa.json`
- Raw law corpus folder present: `data/raw/`
- Scripts are ready to regenerate and validate the dataset

