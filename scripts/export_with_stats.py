import os
import json
import shutil
from datetime import datetime
from collections import Counter

# ================= PATHS =================
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
BASE_FILE = os.path.join(DATA_DIR, "legal_qa.json")

if not os.path.exists(BASE_FILE):
    print("❌ legal_qa.json not found. Run auto_generate_qa.py first.")
    exit(1)

# ================= LOAD DATA =================
with open(BASE_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"\nLoaded dataset with {len(data)} records")

# ================= VERSIONED EXPORT =================
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
versioned_name = f"legal_qa_{timestamp}.json"
versioned_path = os.path.join(DATA_DIR, versioned_name)

shutil.copy(BASE_FILE, versioned_path)
print(f"📦 Versioned copy created: {versioned_name}")

# ================= DATASET STATS =================
total_records = len(data)
laws = set()
word_counts = []
hashes = set()
duplicate_hashes = 0

legal_terms = [
    "shall", "may", "means", "includes",
    "provides", "liable", "entitled",
    "extends", "applies"
]

term_counter = Counter()

for row in data:
    laws.add(row["law"])

    words = row["context"].split()
    word_counts.append(len(words))

    # Duplicate detection
    h = row.get("hash")
    if h in hashes:
        duplicate_hashes += 1
    hashes.add(h)

    # Legal term frequency
    lower_text = row["context"].lower()
    for term in legal_terms:
        if term in lower_text:
            term_counter[term] += 1

avg_words = sum(word_counts) / total_records if total_records else 0

stats = {
    "total_records": total_records,
    "unique_laws": len(laws),
    "average_words_per_section": round(avg_words, 2),
    "longest_section_words": max(word_counts) if word_counts else 0,
    "shortest_section_words": min(word_counts) if word_counts else 0,
    "duplicate_hashes_detected": duplicate_hashes,
    "top_legal_terms": term_counter.most_common(10),
    "generated_at": timestamp
}

# ================= SAVE STATS =================
stats_path = os.path.join(DATA_DIR, "dataset_stats.json")

with open(stats_path, "w", encoding="utf-8") as f:
    json.dump(stats, f, indent=2)

print("\n📊 Dataset Statistics")
print("===================================")
print(f"Total records: {stats['total_records']}")
print(f"Unique laws: {stats['unique_laws']}")
print(f"Average words/section: {stats['average_words_per_section']}")
print(f"Longest section (words): {stats['longest_section_words']}")
print(f"Shortest section (words): {stats['shortest_section_words']}")
print(f"Duplicate hashes detected: {stats['duplicate_hashes_detected']}")
print("Top legal terms:", stats["top_legal_terms"])
print("===================================")

print("\n✅ Export complete.")