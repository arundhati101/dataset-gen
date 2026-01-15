import os
import json
import random
import hashlib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CLAUSE_DIR = os.path.join(BASE_DIR, "data", "clauses")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "legal_qa.jsonl")

def hash_record(q, c):
    return hashlib.sha256((q + c).encode()).hexdigest()

# def classify_clause(text):
#     t = text.lower()
#     if "overtime" in t:
#         return "overtime"
#     if "minimum wage" in t or "minimum rate" in t:
#         return "minimum_wages"
#     if "working day" in t or "hours of work" in t:
#         return "working_hours"
#     if "penalty" in t or "punishable" in t:
#         return "penalty"
#     if "appropriate government" in t:
#         return "authority"
#     return "other"

# Q_MAP = {
#     "overtime": "Is overtime work required to be paid at a higher rate?",
#     "minimum_wages": "Who is responsible for fixing minimum wages?",
#     "working_hours": "Does the law fix normal working hours?",
#     "penalty": "Is there a penalty for violating this provision?",
#     "authority": "Who has authority under this law?",
#     "other": "What does the law state regarding this issue?"
# }

# A_MAP = {
#     "overtime": "Yes, overtime work must be paid at the prescribed overtime rate.",
#     "minimum_wages": "The appropriate Government is responsible for fixing minimum wages.",
#     "working_hours": "Yes, the law provides for fixing normal working hours.",
#     "penalty": "Yes, penalties are prescribed for violations under the law.",
#     "authority": "The appropriate Government has authority under this law.",
#     "other": "The context explains the legal position on this matter."
# }

def classify_clause(text: str) -> str:
    t = text.lower()

    if "means" in t or "shall mean" in t:
        return "definition"

    if "punishable" in t or "imprisonment" in t or "fine" in t:
        return "penalty"

    if "offence" in t or "contravention" in t or "liable" in t:
        return "offence"

    if "appropriate government" in t or "controller" in t or "adjudicating officer" in t:
        return "authority"

    if "may" in t and ("direct" in t or "order" in t or "authorize" in t):
        return "power"

    if "appeal" in t or "procedure" in t or "inquiry" in t:
        return "procedure"

    if "extends to" in t or "shall apply" in t:
        return "applicability"

    return "other"

Q_MAP = {
    "definition": "How is this term defined under the law?",
    "penalty": "What penalty is prescribed under this provision?",
    "offence": "What constitutes an offence under this provision?",
    "authority": "Which authority is empowered under this provision?",
    "power": "What powers are granted under this provision?",
    "procedure": "What procedure is prescribed under this provision?",
    "applicability": "To whom does this law apply?",
    "other": "What does this provision state?"
}

A_MAP = {
    "definition": "The provision defines the relevant term as stated in the context.",
    "penalty": "The provision prescribes penalties as stated in the context.",
    "offence": "The provision specifies acts that constitute an offence.",
    "authority": "The provision identifies the competent authority.",
    "power": "The provision grants specific powers as described.",
    "procedure": "The provision lays down the procedure to be followed.",
    "applicability": "The provision specifies the scope and applicability of the law.",
    "other": "The provision explains the legal position on this matter."
}

existing_hashes = set()
if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE, encoding="utf-8") as f:
        for line in f:
            try:
                existing_hashes.add(json.loads(line)["hash"])
            except:
                pass

new_records = []

for file in os.listdir(CLAUSE_DIR):
    if not file.endswith(".txt"):
        continue

    law_name = file.replace(".txt", "")
    with open(os.path.join(CLAUSE_DIR, file), encoding="utf-8") as f:
        clauses = [c.strip() for c in f.read().split("\n\n")]

    for idx, clause in enumerate(clauses):
        topic = classify_clause(clause)
        q = Q_MAP[topic]
        a = A_MAP[topic]

        h = hash_record(q, clause)
        if h in existing_hashes:
            continue

        record = {
            "id": f"{law_name}_{idx}",
            "law": law_name,
            "question": q,
            "context": clause,
            "answer": a,
            "hash": h
        }

        new_records.append(record)
        existing_hashes.add(h)

with open(OUTPUT_FILE, "a", encoding="utf-8") as out:
    for r in new_records:
        out.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"Added {len(new_records)} new QA records")
