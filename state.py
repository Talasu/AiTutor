"""Student state and scoring. Plain code: the model can never change a score or an answer key."""
from dataclasses import dataclass, field

MASTERED = 0.8   # a skill counts as learned at this score
STEP = 0.15      # score change per answer


@dataclass
class Student:
    topic: str = ""
    skills: dict = field(default_factory=dict)       # id -> {name, needs, score, asked}
    questions: dict = field(default_factory=dict)    # id -> question WITH key (never sent to the agent)
    pending: str = ""                                # id of the question waiting for an answer
    last_graded: dict = field(default_factory=dict)
    misconceptions: list = field(default_factory=list)
    flagged: set = field(default_factory=set)        # questions the student reported as wrong
    log: list = field(default_factory=list)          # every tool call, for your report
    stats: dict = field(default_factory=lambda: {"accepted": 0, "rejected": 0, "bad_format": 0})

    def difficulty(self, skill_id):
        s = self.skills[skill_id]["score"]
        return 1 if s < 0.4 else 2 if s < 0.7 else 3

    def all_mastered(self):
        return bool(self.skills) and all(v["score"] >= MASTERED for v in self.skills.values())

    def suggest(self):
        """Returns (phase, skill_id, difficulty).
        Diagnostic: ask each skill once. Learning: weakest unmastered skill, or its weak prerequisite."""
        unasked = [k for k, v in self.skills.items() if v["asked"] == 0]
        if unasked:
            return "diagnostic", unasked[0], 2
        open_skills = [k for k, v in self.skills.items() if v["score"] < MASTERED]
        if not open_skills:
            return "done", None, None
        target = min(open_skills, key=lambda k: self.skills[k]["score"])
        if self.skills[target]["score"] < 0.4:
            weak_pre = [p for p in self.skills[target]["needs"]
                        if p in self.skills and self.skills[p]["score"] < 0.6]
            if weak_pre:
                target = min(weak_pre, key=lambda k: self.skills[k]["score"])
        return "learning", target, self.difficulty(target)
