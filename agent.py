"""The agent loop.

The model answers each step with ONE JSON object:
    {"say": "text for the student, or empty", "tool": null | {"name": "...", "args": {...}}}
If "tool" is set, we run it, feed back the result, and ask the model again.
When "tool" is null the turn ends. This works with any model, with or without native tool calling.
"""
import json

import llm
import tools

MAX_STEPS = 6   # stops a runaway loop

SYSTEM = """You are an adaptive tutor for ANY topic the student chooses.
Every reply must be ONE JSON object: {"say": "...", "tool": null or {"name": "...", "args": {...}}}

Tools:
- build_skill_map(topic): lists the sub-skills of a topic. Call it when the student names a topic.
- get_student_state(): scores, phase, suggested_skill, suggested_difficulty. Call it before choosing a question.
- generate_verified_question(skill, difficulty, misconception): writes and checks one question. skill is a skill id.
- explain(): after a wrong answer, returns the right answer and the misconception behind the student's choice.

Rules:
- You never grade. The app grades and sends you STUDENT_ANSWERED events.
- Use suggested_skill and suggested_difficulty unless you have a clear reason not to.
- After a wrong answer: call explain, explain the mistake in 2 to 4 simple sentences, then ask a new, easier question.
- After generate_verified_question succeeds, say one short line. The app shows the question and options itself.
  Never repeat the options and never reveal the answer.
- If all_mastered is true, congratulate the student and stop.
- One question at a time. Only use the tools listed above."""


def run_tool(S, name, args):
    fn = tools.TOOLS.get(name)
    if fn is None:
        result = {"error": f"unknown tool '{name}'"}
    else:
        try:
            result = fn(S, **(args or {}))
        except TypeError as e:
            result = {"error": f"bad arguments: {e}"}
    S.log.append({"tool": name, "args": args, "result": result})
    return result


def run_turn(S, history, user_text):
    """history is the model's message list (alternating user / assistant strings). Returns the reply text."""
    history.append({"role": "user", "content": user_text})
    says = []
    for _ in range(MAX_STEPS):
        raw = llm.chat("agent", SYSTEM, history)
        history.append({"role": "assistant", "content": raw})
        act = llm.parse_json(raw) or {"say": raw, "tool": None}
        if act.get("say"):
            says.append(act["say"])
        tool = act.get("tool")
        if not tool:
            return "\n\n".join(says)
        result = run_tool(S, tool.get("name"), tool.get("args"))
        history.append({"role": "user", "content": f"TOOL_RESULT {tool.get('name')}: {json.dumps(result)}"})
    # Too many steps: close the turn so messages keep alternating.
    history.append({"role": "assistant", "content": '{"say": "(stopped after too many steps)", "tool": null}'})
    says.append("(The tutor got stuck. Please try again.)")
    return "\n\n".join(says)


def on_answer(S, history, choice):
    """Grade in plain code, then let the agent react. Returns (grading_result, agent_reply)."""
    result = tools.check_answer(S, choice)
    S.log.append({"tool": "check_answer (app)", "args": {"choice": choice}, "result": result})
    if "error" in result:
        return result, ""
    return result, run_turn(S, history, "STUDENT_ANSWERED " + json.dumps(result))
