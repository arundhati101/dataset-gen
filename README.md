# 📚 DATASET-GEN  
## Legal QA Dataset Generator

Automatically build a structured Question–Answer dataset from raw statutory PDF documents.

---

## 📌 Overview

**DATASET-GEN** transforms unstructured law PDFs into a clean, section-wise QA dataset suitable for:

- Retrieval-Augmented Generation (RAG)
- Legal AI model training
- Clause-level semantic search
- Embedding + FAISS indexing pipelines
- Legal experimentation workflows

The system performs:

- PDF text extraction  
- Document normalization  
- Section-level parsing  
- Template-based question generation  
- SHA-256 hash-based deduplication  
- Structured JSON export  

**Final Output File:**
data/legal_qa.json


---

## 📂 Project Structure
dataset-gen/
├── requirements.txt
├── README.md
│
├── data/
│ ├── legal_qa.json # Generated QA dataset
│ └── raw/ # Source law PDFs
│
└── scripts/
├── auto_generate_qa.py # Main dataset generator
├── check_duplicates.py # Conflict checker
└── remove_duplicates.py # Deduplication utility



---

## ⚙️ Processing Pipeline

### 1️⃣ PDF Extraction

- Reads every `.pdf` file inside `data/raw/`
- Uses `pypdf.PdfReader`
- Extracts all pages into a single document string

---

### 2️⃣ Global Cleanup

Applies normalization to improve consistency:

- Converts CR → LF  
- Removes standalone page numbers  
- Strips amendment markers  
- Removes footnote artifacts  
- Eliminates chapter headings  
- Normalizes whitespace  

---

### 3️⃣ Section Header Normalization

Standardizes headers into a consistent format:

<number>. <Title>


This enables reliable downstream section detection.

---

### 4️⃣ Section Splitting

Uses regex-based detection to:

- Identify numbered sections
- Extract section body text
- Stop extraction at:
  - ALL CAPS headings
  - Definition clauses like `(a) "term"`
  - Inserted sections such as `23A.`

---

### 5️⃣ Quality Filtering

Sections are discarded if:

- Fewer than 20 words  
- Missing legal signal terms such as:

shall, may, means, includes,
provides, liable, entitled,
extends, applies


This ensures only meaningful legal clauses are retained.

---

### 6️⃣ QA Generation

For every valid section:

**Question Template:**

What does Section X of the <Law Name> state?


**Answer:**

- Cleaned section body  
- Stored as both `context` and `answer`  

---

### 7️⃣ Hash-Based Deduplication

Each dataset entry includes a SHA-256 hash generated from:


law + section label + cleaned body


This prevents duplicate entries across multiple PDFs or versions.

---

### 8️⃣ Dataset Export

Final dataset written to:

data/legal_qa.json


---

## 🧾 Output Schema

Each entry in `legal_qa.json`:

```json
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
Conflict Checker

File: scripts/check_duplicates.py

Detects:

Same normalized question

Different answer text

Used to identify inconsistencies across PDF versions.

Run:

python scripts/check_duplicates.py
Hard Deduplication

File: scripts/remove_duplicates.py

Removes:

Duplicate hashes

Duplicate question–answer pairs

Rewrites legal_qa.json with a clean dataset.

Run:

python scripts/remove_duplicates.py
🛠 Setup
1️⃣ Create Virtual Environment
python -m venv .venv

Activate:

Windows (PowerShell)

.\.venv\Scripts\Activate.ps1

Mac/Linux

source .venv/bin/activate
2️⃣ Install Dependencies
pip install -r requirements.txt
▶️ Usage
Generate Dataset
python scripts/auto_generate_qa.py
Check Conflicts
python scripts/check_duplicates.py
Remove Duplicates
python scripts/remove_duplicates.py
🔄 Recommended Workflow

Add or update PDFs inside data/raw/

Run dataset generator

Run conflict checker

Run duplicate remover (if necessary)

Inspect legal_qa.json

Feed into embedding / RAG pipeline

⚠️ Important Notes

Only store PDF files inside data/raw/

Law name is derived from the PDF filename

OCR-heavy or scanned PDFs may reduce extraction quality

Re-running generator overwrites existing dataset

Hash ensures content-level deduplication

📊 Intended Use Cases

Legal Retrieval-Augmented Generation systems

FAISS vector indexing

Clause-level semantic search

QA fine-tuning datasets

Legal AI research experiments

📌 Current Status

Dataset generator stable

Section parser implemented

Hash-based deduplication active

Conflict detection utility available

Dataset ready for embedding pipelines

Version: 1.0
Status: Stable
Output Format: JSON