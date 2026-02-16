import os
import json
import hashlib

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

CLAUSE_DIR = os.path.join(BASE_DIR, "data", "clauses")
OUT_FILE = os.path.join(BASE_DIR, "data", "legal_qa.json")


def make_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def generate_question(clause):
    c = clause.lower()

    if "define" in c or "means" in c:
        return "How is this term defined under the law?"

    if "penalty" in c or "punishable" in c:
        return "What penalty is prescribed under this provision?"

    if "shall" in c:
        return "What obligation does this provision impose?"

    if "may" in c:
        return "What power is granted under this provision?"

    return "What does this legal provision state?"


def generate_answer(clause):
    # simple extractive summary
    return clause[:280] + "..." if len(clause) > 280 else clause


# -------- LOAD EXISTING DATA --------

dataset = []
existing_hashes = set()

if os.path.exists(OUT_FILE):
    try:
        with open(OUT_FILE, "r", encoding="utf-8") as f:
            dataset = json.load(f)
            existing_hashes = {item["hash"] for item in dataset}
    except:
        dataset = []

start_len = len(dataset)


# -------- PROCESS ALL CLAUSE FILES --------

for file in os.listdir(CLAUSE_DIR):
    if not file.endswith(".txt"):
        continue

    law_name = file.replace(".txt", "")
    path = os.path.join(CLAUSE_DIR, file)

    with open(path, "r", encoding="utf-8") as f:
        clauses = [c.strip() for c in f.read().split("\n\n") if len(c.strip()) > 120]

    added = 0

    for i, clause in enumerate(clauses):

        h = make_hash(clause)
        if h in existing_hashes:
            continue

        q = generate_question(clause)
        a = generate_answer(clause)

        item = {
            "id": f"{law_name}_{i}",
            "law": law_name,
            "question": q,
            "context": clause,
            "answer": a,
            "hash": h
        }

        dataset.append(item)
        existing_hashes.add(h)
        added += 1

    print(f"✅ {law_name} → {added} new QA pairs")


# -------- SAVE DATASET --------

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2, ensure_ascii=False)

print(f"\n TOTAL DATASET SIZE: {len(dataset)} (added {len(dataset)-start_len})")
