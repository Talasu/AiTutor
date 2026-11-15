"""Simulated students for your report.  Run:  python simulate.py
Each fake student is weak at ONE skill (answers it right 20% of the time, others 90%).
We measure how often the agent targets the weak skill after the diagnostic phase."""
import json
import random

import agent
from state import Student


def run_session(weak_index=2, turns=24, seed=0, topic="Photosynthesis"):
    random.seed(seed)
    S, H = Student(), []
    agent.run_turn(S, H, topic)
    if not S.skills:
        return None
    weak = list(S.skills)[weak_index]
    n_skills = len(S.skills)
    asked, weak_asked, key_misses = 0, 0, 0
    for _ in range(turns):
        if not S.pending:
            key_misses += 1
            break
        q = S.questions[S.pending]
        p_right = 0.2 if q["skill"] == weak else 0.9
        wrong = [l for l in q["options"] if l != q["key"]]
        choice = q["key"] if random.random() < p_right else random.choice(wrong)
        asked += 1
        if asked > n_skills and q["skill"] == weak:   # after the diagnostic round
            weak_asked += 1
        agent.on_answer(S, H, choice)
    after = max(0, asked - n_skills)
    return {"weak_skill": weak, "questions": asked,
            "after_diagnostic": after,
            "weak_share": round(weak_asked / after, 2) if after else None,
            "baseline_share": round(1 / n_skills, 2),
            "final_scores": {k: round(v["score"], 2) for k, v in S.skills.items()},
            "stats": S.stats, "stuck": bool(key_misses)}


if __name__ == "__main__":
    runs = [run_session(weak_index=i % 4, seed=i) for i in range(8)]
    for r in runs:
        print(json.dumps(r))
    shares = [r["weak_share"] for r in runs if r and r["weak_share"] is not None]
    if shares:
        print(f"\nAverage share of questions on the weak skill: {sum(shares) / len(shares):.2f} "
              f"(random choice would give {runs[0]['baseline_share']})")
