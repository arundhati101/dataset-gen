# Legal QA Dataset Generator

A project for extracting structured legal question-answer pairs from PDF statutes and maintaining a clean QA dataset.

## 📋 Table of Contents

- [Features](#-features)
- [Project Structure](#-project-structure)
- [Setup](#-setup)
- [Usage](#-usage)
- [Workflow](#-recommended-workflow)
- [Scripts Overview](#-scripts-overview)
- [Dependencies](#dependencies)
- [Notes](#notes)
- [Troubleshooting](#troubleshooting)

## ✨ Features

- 📄 Extracts numbered legal sections from PDF files
- 🧹 Cleans and normalizes legal text for reliable section parsing
- 🤖 Converts section text into QA records
- 🔍 Detects conflicting answers for identical questions
- 🗑️ Removes duplicate dataset entries
- 📊 Exports dataset statistics and versioned backups

## 📁 Project Structure

```
dataset-gen/
├── data/
│   ├── raw/                        # Input PDF files
│   ├── legal_qa.json               # Generated QA dataset
│   ├── dataset_stats.json          # Exported dataset statistics
│   └── legal_qa_<timestamp>.json   # Versioned dataset backups
├── scripts/
│   ├── auto_generate_qa.py         # Main QA generation script
│   ├── check_duplicates.py         # Conflict detection tool
│   ├── remove_duplicates.py        # Deduplication utility
│   ├── export_with_stats.py        # Versioned export and stats generator
│   └── tempCodeRunnerFile.py       # Temporary duplicate of main generator
├── requirements.txt                # Python dependency list
└── README.md                       # This file
```

## 🛠 Setup

### 1️⃣ Create a virtual environment

```bash
python -m venv .venv
```

### 2️⃣ Activate the environment

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Mac/Linux:**

```bash
source .venv/bin/activate
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

## ▶️ Usage

### Generate the QA dataset

```bash
python scripts/auto_generate_qa.py
```

- Reads `.pdf` files from `data/raw/`
- Extracts and cleans text
- Splits legal sections into QA records
- Writes `data/legal_qa.json`

### Check for conflicts

```bash
python scripts/check_duplicates.py
```

- Finds questions with multiple distinct answers
- Helps identify inconsistent or duplicate entries

### Remove duplicates

```bash
python scripts/remove_duplicates.py
```

- Removes duplicate hashes
- Removes duplicate `(question, answer)` pairs
- Saves a cleaned dataset

### Export dataset and stats

```bash
python scripts/export_with_stats.py
```

- Creates a timestamped backup copy
- Writes dataset metrics to `data/dataset_stats.json`

## 🔄 Recommended workflow

1. Place PDF documents in `data/raw/`
2. Run `python scripts/auto_generate_qa.py`
3. Run `python scripts/check_duplicates.py`
4. Run `python scripts/remove_duplicates.py`
5. Run `python scripts/export_with_stats.py`
6. Review `data/legal_qa.json` and `data/dataset_stats.json`
7. Use the clean dataset in downstream RAG/chatbot pipelines

## 📝 Scripts Overview

### `scripts/auto_generate_qa.py`

This is the main dataset builder.

What it does:
- Reads PDF content using `pypdf`
- Cleans page text and removes noise
- Normalizes section headers such as `12.`
- Extracts numbered sections from the document
- Filters out short or irrelevant text blocks
- Builds JSON records with `id`, `law`, `section`, `question`, `context`, `answer`, and `hash`

### `scripts/check_duplicates.py`

This script detects inconsistent answers.

What it does:
- Loads `data/legal_qa.json`
- Normalizes question text for grouping
- Finds questions with more than one unique answer
- Prints conflict details and a summary count

### `scripts/remove_duplicates.py`

This script deduplicates the dataset.

What it does:
- Loads `data/legal_qa.json`
- Removes entries with duplicate hashes
- Removes exact duplicate question-answer rows
- Writes the cleaned dataset back to disk

### `scripts/export_with_stats.py`

This script exports a versioned dataset copy and generates statistics.

What it does:
- Copies `data/legal_qa.json` to `data/legal_qa_<timestamp>.json`
- Computes metrics such as total records, unique laws, average section length, and duplicate hashes
- Saves summary stats to `data/dataset_stats.json`

### `scripts/tempCodeRunnerFile.py`

This is a temporary duplicate of the main generator script and is not part of the core workflow.

## Dependencies

The full dependency list is in `requirements.txt`.

Current scripts use:
- `pypdf` for PDF text extraction
- Python standard library modules: `os`, `json`, `re`, `hashlib`, `collections`, `datetime`, `shutil`

The repository also contains broader ML/RAG-focused packages in `requirements.txt`, but the present script set does not require them.

## Notes

- `data/legal_qa.json` is the main generated QA dataset.
- `data/dataset_stats.json` is produced by `export_with_stats.py`.
- `data/raw/` must contain PDFs before running the generator.
- The script flow is repeatable for new legal documents.

## Troubleshooting

### PDF extraction fails

- Confirm the PDF is not password-protected
- Confirm the file is in `data/raw/`

### No entries in `legal_qa.json`

- Confirm the PDF contains numbered sections
- Confirm the text passes the script's quality filters

### Duplicate records remain

- Run `python scripts/check_duplicates.py`
- Run `python scripts/remove_duplicates.py`

## Manager presentation notes

1. Explain the goal: convert legal PDFs into a structured QA dataset.
2. Show the input folder and generated output file.
3. Walk through the main scripts: generate, check, clean, export.
4. Highlight that the process is repeatable and version-controlled.
