import os
import json
from collections import defaultdict

# -----------------------------
# Build file path
# -----------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "legal_qa.json")

# -----------------------------
# Load JSON data
# -----------------------------
with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# -----------------------------
# Map questions to rows
# -----------------------------
q_map = defaultdict(list)

for row in data:
    question = row["question"].strip().lower()
    q_map[question].append(row)

# -----------------------------
# Print conflicting questions
# -----------------------------
conflicting_questions = 0
conflicting_rows = 0

for question, rows in q_map.items():
    # Get unique answers
    unique_answers = set(r["answer"].strip() for r in rows)
    
    if len(unique_answers) > 1:
        conflicting_questions += 1
        conflicting_rows += len(unique_answers)

        print("=" * 100)
        print("QUESTION:")
        print(question)
        print("\nANSWERS:")
        
        for i, ans in enumerate(unique_answers, 1):
            print(f"{i}. {ans}")
        
        print(f"\nTotal unique conflicting answers: {len(unique_answers)}\n")

# Summary
print("\n" + "#" * 100)
print("SUMMARY")
print("Conflicting Questions:", conflicting_questions)
print("Total Conflicting Answer Variations:", conflicting_rows)