import os
import json

# -----------------------------
# Paths
# -----------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "legal_qa.json")

# -----------------------------
# Load dataset
# -----------------------------
with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Original dataset size: {len(data)}")

# -----------------------------
# Remove duplicates
# -----------------------------
seen_hashes = set()
seen_pairs = set()

cleaned_data = []
removed = 0

for row in data:
    h = row.get("hash", "").strip()
    q = row.get("question", "").strip().lower()
    a = row.get("answer", "").strip()

    qa_pair = (q, a)

    # If hash already seen → duplicate
    if h in seen_hashes:
        removed += 1
        continue

    # Extra safety: if same question+answer seen → duplicate
    if qa_pair in seen_pairs:
        removed += 1
        continue

    seen_hashes.add(h)
    seen_pairs.add(qa_pair)
    cleaned_data.append(row)

# -----------------------------
# Save cleaned dataset
# -----------------------------
with open(DATA_PATH, "w", encoding="utf-8") as f:
    json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

print(f"Duplicates removed: {removed}")
print(f"Final dataset size: {len(cleaned_data)}")
print("Done ✅")