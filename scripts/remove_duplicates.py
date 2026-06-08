import os
import json
import shutil
from collections import Counter, defaultdict

# -----------------------------
# Paths
# -----------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
DATA_PATH = os.path.join(DATA_DIR, 'legal_qa.json')
BACKUP_PATH = os.path.join(DATA_DIR, 'legal_qa_pre_cleanup.json')

# -----------------------------
# Load dataset
# -----------------------------
if not os.path.exists(DATA_PATH):
    print('legal_qa.json not found. Run auto_generate_qa.py first.')
    exit(1)

shutil.copy(DATA_PATH, BACKUP_PATH)
print(f'Backup created: {os.path.basename(BACKUP_PATH)}')

with open(DATA_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f'Original dataset size: {len(data)}')

# -----------------------------
# Remove exact duplicates
# -----------------------------
seen_hashes = set()
seen_pairs = set()

deduped_data = []
exact_duplicates_removed = 0

for row in data:
    h = row.get('hash', '').strip()
    q = row.get('question', '').strip().lower()
    a = row.get('answer', '').strip()

    qa_pair = (q, a)

    if h and h in seen_hashes:
        exact_duplicates_removed += 1
        continue

    if qa_pair in seen_pairs:
        exact_duplicates_removed += 1
        continue

    if h:
        seen_hashes.add(h)
    seen_pairs.add(qa_pair)
    deduped_data.append(row)

# -----------------------------
# Resolve conflicting answers
# -----------------------------
question_groups = defaultdict(list)
for row in deduped_data:
    question = row['question'].strip().lower()
    question_groups[question].append(row)

resolved_data = []
conflict_questions = 0
conflict_variants_removed = 0

for question, rows in question_groups.items():
    if len(rows) == 1:
        resolved_data.append(rows[0])
        continue

    conflict_questions += 1
    answer_counts = Counter(row['answer'].strip() for row in rows)
    canonical_answer, _ = answer_counts.most_common(1)[0]

    candidate_rows = [row for row in rows if row['answer'].strip() == canonical_answer]
    chosen_row = candidate_rows[0]
    resolved_data.append(chosen_row)
    conflict_variants_removed += len(rows) - 1

    print(f'Resolved conflict for question: {question}')
    print(f'  Kept answer variant with {answer_counts[canonical_answer]} occurrence(s)')

# -----------------------------
# Save cleaned dataset
# -----------------------------
with open(DATA_PATH, 'w', encoding='utf-8') as f:
    json.dump(resolved_data, f, indent=2, ensure_ascii=False)

print(f'Exact duplicates removed: {exact_duplicates_removed}')
print(f'Conflicting variants removed: {conflict_variants_removed}')
print(f'Conflicting questions collapsed: {conflict_questions}')
print(f'Final dataset size: {len(resolved_data)}')
print('Done')