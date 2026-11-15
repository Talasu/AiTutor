"""Tools. The agent can call build_skill_map, get_student_state, generate_verified_question, explain.
check_answer is NOT an agent tool: the app calls it when the student clicks, so grading never depends on the model."""
import random

import llm
from state import STEP, MASTERED

TRIES = 3        # attempts to produce one verified question
N_SOLVES = 3     # independent solver runs; all must match the key
LETTERS = "ABCD"

SKILLMAP_SYSTEM = (
    "You design learning plans. Return ONLY JSON: "
    '{"skills":[{"id":"snake_case_id","name":"Short name","needs":["ids that must come first"]}]}. '
    "Give 5 to 8 skills ordered from foundations to advanced. 'needs' may only list earlier ids.")

GEN_SYSTEM = (
    "You write one multiple-choice question. Return ONLY JSON: "
    '{"question":"...","correct":"the one right answer","wrong":['
    '{"text":"...","misconception":"short_snake_case"},{"text":"...","misconception":"..."},'
    '{"text":"...","misconception":"..."}],"explanation":"2 sentences on why the correct answer is right"}. '
    "Difficulty 1 = recall, 2 = apply, 3 = tricky reasoning. Exactly one option must be clearly correct. "
    "Each wrong option must be plausible but definitely wrong, and reflect a real misconception. "
    "If a target misconception is given, make one wrong option match it.")

SOLVE_SYSTEM = "Answer the multiple-choice question. Reply with ONLY the letter of the best answer."


# ------------------------------------------------------------------ skill map
def _valid_map(m):
    if not isinstance(m, dict) or not isinstance(m.get("skills"), list):
        return False
    seen = []
    if not 4 <= len(m["skills"]) <= 8:
        return False
    for s in m["skills"]:
        if not isinstance(s, dict) or not s.get("id") or not s.get("name") or s["id"] in seen:
            return False
        if not isinstance(s.get("needs", []), list) or any(n not in seen for n in s.get("needs", [])):
            return False
        seen.append(s["id"])
    return True


def build_skill_map(S, topic):
    for _ in range(TRIES):
        m = llm.parse_json(llm.chat("skillmap", SKILLMAP_SYSTEM,
                                    [{"role": "user", "content": f"TOPIC: {topic}"}]))
        if _valid_map(m):
            S.topic = topic
            S.skills = {s["id"]: {"name": s["name"], "needs": s.get("needs", []),
                                  "score": 0.5, "asked": 0} for s in m["skills"]}
            return {"topic": topic, "skills": [{"id": s["id"], "name": s["name"],
                                                "needs": s.get("needs", [])} for s in m["skills"]]}
    return {"error": "could not build a valid skill map"}


# ------------------------------------------------------------------ state
def get_student_state(S):
    if not S.skills:
        return {"error": "no topic yet, call build_skill_map first"}
    phase, skill, diff = S.suggest()
    return {
        "topic": S.topic,
        "phase": phase,
        "scores": {k: round(v["score"], 2) for k, v in S.skills.items()},
        "mastered": [k for k, v in S.skills.items() if v["score"] >= MASTERED],
        "recent_misconceptions": S.misconceptions[-3:],
        "all_mastered": S.all_mastered(),
        "suggested_skill": skill,
        "suggested_difficulty": diff,
    }


# ------------------------------------------------------------------ questions
def _build(q):
    """Validate the model's JSON, shuffle the options in code, and keep the key in code."""
    try:
        wrong = q["wrong"]
        if len(wrong) != 3 or not q["question"] or not q["correct"] or not q["explanation"]:
            return None
        items = [(str(q["correct"]), None)] + [(str(w["text"]), str(w["misconception"])) for w in wrong]
        if len({t.strip().lower() for t, _ in items}) != 4:
            return None
    except (KeyError, TypeError):
        return None
    random.shuffle(items)
    options = {LETTERS[i]: t for i, (t, _) in enumerate(items)}
    key = next(LETTERS[i] for i, (t, m) in enumerate(items) if m is None)
    miscs = {LETTERS[i]: m for i, (t, m) in enumerate(items) if m is not None}
    return {"question": q["question"], "options": options, "key": key,
            "misconceptions": miscs, "explanation": q["explanation"]}


def _verify(built):
    """Solve the question N times without the key. Accept only if every run matches."""
    text = built["question"] + "\n" + "\n".join(f"{l}. {t}" for l, t in built["options"].items())
    for _ in range(N_SOLVES):
        ans = llm.chat("solve", SOLVE_SYSTEM, [{"role": "user", "content": text}], temperature=0.3)
        if not ans or ans.strip().upper()[:1] != built["key"]:
            return False
    return True


def generate_verified_question(S, skill, difficulty=2, misconception=None):
    if skill not in S.skills:
        return {"error": f"unknown skill '{skill}'"}
    try:
        difficulty = max(1, min(3, int(difficulty)))
    except (TypeError, ValueError):
        difficulty = 2
    prompt = (f"TOPIC: {S.topic}\nSKILL: {S.skills[skill]['name']}\nDIFFICULTY: {difficulty}\n"
              f"TARGET MISCONCEPTION: {misconception or 'none'}")
    for _ in range(TRIES):
        built = _build(llm.parse_json(llm.chat("generate", GEN_SYSTEM,
                                               [{"role": "user", "content": prompt}])))
        if not built:
            S.stats["bad_format"] += 1
            continue
        if not _verify(built):
            S.stats["rejected"] += 1
            continue
        qid = f"q{len(S.questions) + 1}"
        built.update(id=qid, skill=skill, difficulty=difficulty)
        S.questions[qid] = built
        S.pending = qid
        S.stats["accepted"] += 1
        # The key is NOT returned: the agent never sees the answer.
        return {"question_id": qid, "skill": skill,
                "question": built["question"], "options": built["options"]}
    return {"error": "could not produce a verified question"}


# ------------------------------------------------------------------ grading (app only)
def check_answer(S, choice):
    choice = str(choice).strip().upper()[:1]
    q = S.questions.get(S.pending)
    if not q:
        return {"error": "no question is waiting for an answer"}
    if choice not in q["options"]:
        return {"error": f"'{choice}' is not one of the options"}
    correct = choice == q["key"]
    sk = S.skills[q["skill"]]
    sk["score"] = max(0.0, min(1.0, sk["score"] + (STEP if correct else -STEP)))
    sk["asked"] += 1
    if not correct:
        S.misconceptions.append(q["misconceptions"][choice])
    S.last_graded = {"choice": choice, "correct": correct, "q": q}
    S.pending = ""
    return {"correct": correct, "right_answer": q["key"], "skill": sk["name"],
            "new_score": round(sk["score"], 2)}


def explain(S):
    g = S.last_graded
    if not g:
        return {"error": "nothing has been graded yet"}
    q = g["q"]
    return {"skill": S.skills[q["skill"]]["name"],
            "student_answer": q["options"][g["choice"]],
            "right_answer": q["options"][q["key"]],
            "misconception": q["misconceptions"].get(g["choice"]),
            "explanation": q["explanation"]}


TOOLS = {
    "build_skill_map": build_skill_map,
    "get_student_state": get_student_state,
    "generate_verified_question": generate_verified_question,
    "explain": explain,
}
