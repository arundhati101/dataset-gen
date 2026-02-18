import os
import json
import hashlib
import re

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CLAUSE_DIR = os.path.join(BASE_DIR, "data", "clauses")
OUT_FILE = os.path.join(BASE_DIR, "data", "legal_qa.json")


# ================= HASH =================
def make_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ================= CLEAN TEXT =================
def clean(text):

    text = re.sub(r"\s+", " ", text)

    # remove state amendments / notes
    text = re.split(r"STATE AMENDMENTS|Vide .*? Act", text, flags=re.I)[0]

    # remove footnote numbers like 1*** or 2
    text = re.sub(r"\d+\*+", "", text)

    # remove stray numbering artifacts
    text = re.sub(r"\s+\d+\s+", " ", text)

    return text.strip()


# ================= VALID CLAUSE =================
def is_valid_clause(c):
    if len(c) < 120:
        return False
    if len(c.split()) < 15:
        return False

    junk = [
        "an act to",
        "chapter i",
        "schedule",
        "printed by",
        "ministry of"
    ]

    if any(x in c.lower() for x in junk):
        return False

    return True


# ================= EXTRACT SECTION =================
def extract_section(clause):

    # Section like "6. Legitimacy..."
    sec = re.search(r"^(\d+)\.", clause)
    if sec:
        return f"Section {sec.group(1)}"

    # sub-section like (2)
    sub = re.search(r"^\((\d+)\)", clause)
    if sub:
        return f"Sub-section ({sub.group(1)})"

    # clause like (a)
    cl = re.search(r"^\(([a-z])\)", clause)
    if cl:
        return f"Clause ({cl.group(1)})"

    return "this provision"


# ================= DETECT LEGAL TOPIC =================
def detect_topic(clause):
    lc = clause.lower()

    if "extends to the whole of india" in lc:
        return "extent"

    if "come into force" in lc:
        return "commencement"

    if '" ' in clause and "means" in lc:
        return "definition"

    if "void" in lc or "voidable" in lc:
        return "validity"

    if "petition" in lc or "filed" in lc:
        return "procedure"

    if "district court" in lc and "jurisdiction" in lc:
        return "jurisdiction"

    if "maintenance" in lc:
        return "maintenance"

    if "custody" in lc:
        return "custody"

    if "punishable" in lc or "imprisonment" in lc:
        return "penalty"

    if "may make an order" in lc or "may issue" in lc:
        return "court_power"

    return "rule"


# ================= EXTRACT CORE RULE =================
def core_rule(clause):

    clause = clean(clause)

    # remove numbering like (1) or 6.
    clause = re.sub(r"^\(\d+\)\s*", "", clause)
    clause = re.sub(r"^\d+\.\s*", "", clause)

    # shorten very long clauses to first 2 sentences
    parts = clause.split(". ")
    if len(parts) > 2:
        clause = ". ".join(parts[:2])

    return clause.strip()


# ================= GENERATE QA =================
def generate_qa(clause, law):

    clause = clean(clause)
    rule = core_rule(clause)

    section = extract_section(clause)
    topic = detect_topic(clause)

    qa = []

    # ---------- EXTENT ----------
    if topic == "extent":
        q = f"What is the territorial extent of the {law} under {section}?"
        a = f"Under {section} of the {law}, {rule}"

    # ---------- COMMENCEMENT ----------
    elif topic == "commencement":
        q = f"What does {section} of the {law} provide regarding commencement of the Act?"
        a = f"{section} of the {law} states that {rule}"

    # ---------- DEFINITION ----------
    elif topic == "definition":
        term = re.search(r'"([^"]+)"', clause)
        if term:
            term = term.group(1)
            q = f"How is '{term}' defined under the {law} in {section}?"
            a = f"Under {section} of the {law}, {term} is defined as: {rule}"
        else:
            q = f"What definition is given in {section} of the {law}?"
            a = f"{section} of the {law} provides that {rule}"

    # ---------- VALIDITY ----------
    elif topic == "validity":
        q = f"What does {section} of the {law} state about validity of marriage?"
        a = f"{section} of the {law} provides that {rule}"

    # ---------- PROCEDURE ----------
    elif topic == "procedure":
        q = f"What procedural requirement is provided in {section} of the {law}?"
        a = f"{section} of the {law} requires that {rule}"

    # ---------- JURISDICTION ----------
    elif topic == "jurisdiction":
        q = f"What jurisdiction rule is provided in {section} of the {law}?"
        a = f"{section} of the {law} provides that {rule}"

    # ---------- MAINTENANCE ----------
    elif topic == "maintenance":
        q = f"What does {section} of the {law} provide regarding maintenance?"
        a = f"{section} of the {law} states that {rule}"

    # ---------- CUSTODY ----------
    elif topic == "custody":
        q = f"What does {section} of the {law} provide regarding custody of children?"
        a = f"{section} of the {law} provides that {rule}"

    # ---------- COURT POWER ----------
    elif topic == "court_power":
        q = f"What power is granted to the court in {section} of the {law}?"
        a = f"{section} of the {law} authorises that {rule}"

    # ---------- PENALTY ----------
    elif topic == "penalty":
        q = f"What punishment is prescribed in {section} of the {law}?"
        a = f"{section} of the {law} prescribes that {rule}"

    # ---------- GENERAL ----------
    else:
        q = f"What legal rule is provided in {section} of the {law}?"
        a = f"{section} of the {law} states that {rule}"

    qa.append((q, a))
    return qa


# ================= LOAD EXISTING =================
def load_existing():
    if not os.path.exists(OUT_FILE):
        return [], set()

    try:
        with open(OUT_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d, {x["hash"] for x in d}
    except:
        return [], set()


# ================= SAVE =================
def save(data):
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ================= MAIN =================
def main():

    dataset, hashes = load_existing()
    start = len(dataset)

    for file in os.listdir(CLAUSE_DIR):

        if not file.endswith(".txt"):
            continue

        law = file[:-4]
        path = os.path.join(CLAUSE_DIR, file)

        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()

        raw_clauses = [c.strip() for c in raw.split("\n\n")]
        clauses = [c for c in raw_clauses if is_valid_clause(c)]

        added = 0

        for i, clause in enumerate(clauses):

            h = make_hash(clause)
            if h in hashes:
                continue

            qa_pairs = generate_qa(clause, law)

            for q_i, (q, a) in enumerate(qa_pairs):
                dataset.append({
                    "id": f"{law}_{i}_{q_i}",
                    "law": law,
                    "question": q,
                    "context": clause,
                    "answer": a,
                    "hash": h
                })

            hashes.add(h)
            added += len(qa_pairs)

        print(f"📘 {law} → {added} QA pairs")

    save(dataset)

    print("===================================")
    print(f"TOTAL DATASET SIZE: {len(dataset)}")
    print(f"NEWLY ADDED: {len(dataset)-start}")
    print("===================================")


if __name__ == "__main__":
    main()
