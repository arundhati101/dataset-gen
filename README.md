# Legal QA Dataset Generator

A comprehensive tool for extracting, generating, and managing question-answer pairs from legal PDF documents with built-in conflict detection and deduplication.

## 📋 Table of Contents

- [Features](#-features)
- [Project Structure](#-project-structure)
- [Setup](#-setup)
- [Usage](#-usage)
- [Workflow](#-recommended-workflow)
- [Scripts Overview](#-scripts-overview)

## ✨ Features

- 📄 **Automated QA Generation** from legal PDF documents
- 🔍 **Conflict Detection** for inconsistent answers
- 🗑️ **Smart Deduplication** with hash-based comparison
- 🎯 **Normalized Question Matching** for better accuracy
- 📊 **Clean JSON Output** ready for RAG pipelines

## 📁 Project Structure
```
legal-qa-dataset/
├── data/
│   ├── raw/                    # Place your PDF files here
│   └── legal_qa.json           # Generated QA dataset
├── scripts/
│   ├── auto_generate_qa.py     # Main QA generation script
│   ├── check_duplicates.py     # Conflict detection tool
│   └── remove_duplicates.py    # Deduplication utility
├── .venv/                      # Virtual environment (auto-generated)
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🛠 Setup

### 1️⃣ Create Virtual Environment
```bash
python -m venv .venv
```

### 2️⃣ Activate Environment

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Mac/Linux:**
```bash
source .venv/bin/activate
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

## ▶️ Usage

### Generate QA Dataset

Extract questions and answers from PDFs in the `data/raw/` directory:
```bash
python scripts/auto_generate_qa.py
```

**Output:** Creates/updates `data/legal_qa.json`

### Check for Conflicts

Detect inconsistencies where the same question has different answers:
```bash
python scripts/check_duplicates.py
```

**Purpose:** Identifies conflicts across different PDF versions

### Remove Duplicates

Clean the dataset by removing duplicate entries:
```bash
python scripts/remove_duplicates.py
```

**Action:** Rewrites `legal_qa.json` with deduplicated data

## 🔄 Recommended Workflow

Follow this sequence for optimal results:

1. **Prepare Data**  
   Place your PDF documents in `data/raw/`

2. **Generate Dataset**  
```bash
   python scripts/auto_generate_qa.py
```

3. **Check for Conflicts**  
```bash
   python scripts/check_duplicates.py
```

4. **Remove Duplicates** (if needed)  
```bash
   python scripts/remove_duplicates.py
```

5. **Inspect Output**  
   Review `data/legal_qa.json` for quality

6. **Deploy to Pipeline**  
   Feed the clean dataset into your RAG/embedding pipeline

## 📝 Scripts Overview

### 🔎 Conflict Checker

**File:** `scripts/check_duplicates.py`

Detects cases where the same normalized question has different answer text. Used to identify inconsistencies across different PDF versions.

**Key Features:**
- Normalizes questions for accurate matching
- Flags conflicts with detailed reporting
- Non-destructive analysis

### 🗑️ Hard Deduplication

**File:** `scripts/remove_duplicates.py`

Removes duplicate hashes and duplicate question-answer pairs. Rewrites `legal_qa.json` with a clean dataset.

**Key Features:**
- Hash-based duplicate detection
- Content-aware deduplication
- Automatic backup creation (optional)

### 🤖 QA Generator

**File:** `scripts/auto_generate_qa.py`

Automatically extracts and generates question-answer pairs from legal PDF documents.

**Key Features:**
- PDF text extraction
- AI-powered QA generation
- Batch processing support
- Error handling and logging

## 📦 Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`

**Core Libraries:**
- `PyPDF2` or `pdfplumber` - PDF text extraction
- `transformers` or API client - QA generation
- `json` - Data serialization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request


## 💡 Tips

- **Regular Backups:** Always backup `legal_qa.json` before running deduplication
- **PDF Quality:** Higher quality PDFs yield better QA pairs
- **Batch Processing:** Process PDFs in batches for large datasets
- **Version Control:** Track changes to your dataset using Git

## 🐛 Troubleshooting

### Common Issues

**Issue:** Script fails to read PDF  
**Solution:** Ensure PDF is not password-protected or corrupted

**Issue:** Duplicate detection not working  
**Solution:** Run conflict checker before deduplication

**Issue:** Memory errors with large PDFs  
**Solution:** Process PDFs individually or increase system RAM

## 📞 Support

For issues, questions, or contributions, please [open an issue](your-repo-link) on GitHub.

**Made with ❤️ for Legal Tech**