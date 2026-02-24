import os
import json
from collections import defaultdict

# -----------------------------
# Build file path
# -----------------------------
# PROJECT_ROOT goes two levels up from this script's location (scripts/ → project root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "legal_qa.json")  # Path to the QA dataset

# -----------------------------
# Load JSON data
# -----------------------------
# Load the entire legal_qa.json into memory as a list of dicts
with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# -----------------------------
# Map questions to rows
# -----------------------------
# defaultdict(list) automatically creates an empty list for any new key,
# so we don't need to check "if key in dict" before appending
q_map = defaultdict(list)

for row in data:
    # Normalize the question: strip whitespace + lowercase
    # This ensures "What does Section 2 state?" and "what does section 2 state? "
    # are treated as the same question
    question = row["question"].strip().lower()
    q_map[question].append(row)   # Group all rows that share the same question text

# -----------------------------
# Print conflicting questions
# -----------------------------
# A "conflict" means: same question string but different answer texts.
# This can happen when the same section appears in two PDFs with slight text differences,
# or when auto_generate_qa.py produced different body text for the same section.

conflicting_questions = 0   # How many unique questions have conflicting answers
conflicting_rows = 0        # Total number of conflicting answer variants across all questions

for question, rows in q_map.items():
    # Collect the set of unique answers for this question
    # Using a set() automatically deduplicates identical answers
    unique_answers = set(r["answer"].strip() for r in rows)
    
    # If more than one unique answer exists → genuine conflict
    if len(unique_answers) > 1:
        conflicting_questions += 1
        conflicting_rows += len(unique_answers)  # Count each unique variant as one conflict

        print("=" * 100)
        print("QUESTION:")
        print(question)
        print("\nANSWERS:")
        
        # Print each conflicting answer variant with an index number
        for i, ans in enumerate(unique_answers, 1):   # enumerate starts from 1 for readability
            print(f"{i}. {ans}")
        
        print(f"\nTotal unique conflicting answers: {len(unique_answers)}\n")

# Summary — printed after all conflicts have been shown
print("\n" + "#" * 100)
print("SUMMARY")
print("Conflicting Questions:", conflicting_questions)          # How many questions are affected
print("Total Conflicting Answer Variations:", conflicting_rows) # Total answer variants involved