"""Run with:  python -m streamlit run app.py
Everything lives in st.session_state because Streamlit reruns this script on every click."""
import html

import streamlit as st

import agent
from state import Student, MASTERED

st.set_page_config(page_title="Adaptive tutor", layout="wide", initial_sidebar_state="expanded")

STARTERS = ["Photosynthesis", "Python loops and functions",
            "How neural networks learn", "Basic Arabic grammar"]
LEVELS = {1: "Easy", 2: "Medium", 3: "Hard"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;500;600&display=swap');
html, body, .stApp, button, input, textarea { font-family: 'Lexend', system-ui, sans-serif; }

/* page surfaces: set explicitly so dark mode cannot clash */
.stApp, [data-testid="stAppViewContainer"] { background: #F5F7FB !important; }
.stApp::before { content: ""; position: fixed; top: 0; left: 0; right: 0; height: 3px;
  background: #2F5BEA; z-index: 1000000; }
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stDecoration"], footer { display: none !important; }
[data-testid="stBottom"], [data-testid="stBottom"] > div { background: #F5F7FB !important; }
[data-testid="stChatInput"] { background: #FFFFFF !important; border: 1px solid #D5DCEB !important;
  border-radius: 14px !important; }
[data-testid="stChatInput"] textarea { color: #14213D !important; background: transparent !important; }
[data-testid="stChatInput"] textarea::placeholder { color: #7B889F !important; }
.block-container { max-width: 880px; padding-top: 2.4rem; padding-bottom: 6rem; }
section[data-testid="stSidebar"] { background: #FFFFFF !important; border-right: 1px solid #E3E8F2; }

/* text */
.stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown strong { color: #14213D; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: #5B6B86 !important; }
section[data-testid="stSidebar"] summary, section[data-testid="stSidebar"] summary p { color: #14213D !important; }
.stMarkdown h1.h1 { font-size: 2rem; font-weight: 600; color: #14213D; letter-spacing: -0.02em; line-height: 1.2; margin: 0 0 .5rem; }
.stMarkdown p.sub { color: #51607A; font-size: 1rem; line-height: 1.6; max-width: 60ch; margin: 0 0 1.4rem; }

/* steps on the start screen */
.steps { display: flex; gap: .75rem; margin: 0 0 1.6rem; }
.step { flex: 1; display: flex; align-items: center; gap: .7rem; background: #FFFFFF; border: 1px solid #E3E8F2;
  border-radius: 12px; padding: .8rem .9rem; font-size: .92rem; font-weight: 500; color: #14213D; }
.n { display: inline-flex; align-items: center; justify-content: center; width: 1.6rem; height: 1.6rem;
  border-radius: 50%; background: #2F5BEA; color: #FFFFFF; font-size: .8rem; font-weight: 600; flex: none; }

.h1, .sub, .step, .q, .chip, .sname, .brand, .ring-cap, .ring span, .tag, .fb, .done,
.stMarkdown p, .stMarkdown li, [data-testid="stCaptionContainer"] p,
[data-testid="stChatMessage"] p { font-family: 'Lexend', system-ui, sans-serif; }

/* buttons: topic cards and answer tiles */
.stButton, [data-testid="stButton"] { width: 100%; }
.stButton > button { width: 100%; min-height: 3.2rem; justify-content: flex-start; text-align: left;
  background: #FFFFFF; color: #14213D; border: 1px solid #D5DCEB; border-radius: 12px;
  padding: .7rem 1rem; font-weight: 500; transition: border-color .15s, background .15s; }
.stButton > button > div { justify-content: flex-start; }
.stButton > button p { margin: 0; text-align: left; color: inherit; }
.stButton > button:hover { border-color: #2F5BEA; background: #F0F4FF; color: #14213D; }

/* chat bubbles */
[data-testid="stChatMessage"] { background: #FFFFFF; border: 1px solid #E3E8F2; border-radius: 14px;
  padding: .9rem 1rem; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { background: #EAF0FF; border-color: #D3DFFB; }
[data-testid="stChatMessage"] p { color: #14213D; }

/* question card */
[data-testid="stVerticalBlockBorderWrapper"] { background: #FFFFFF; border-radius: 16px; border-color: #E3E8F2; }
.chips { display: flex; gap: .5rem; margin-bottom: .6rem; }
.chip { font-size: .78rem; font-weight: 500; padding: .15rem .65rem; border-radius: 999px; background: #EEF1F8; color: #3B4A66; }
.q { font-size: 1.15rem; font-weight: 500; color: #14213D; line-height: 1.5; margin: .2rem 0 1rem; }
.fb { display: inline-block; font-size: .8rem; font-weight: 500; padding: .15rem .65rem; border-radius: 999px; margin-bottom: .4rem; }
.fb.good { background: #DDF4EA; color: #14694A; }
.fb.bad { background: #FDE5E3; color: #9B2C26; }
.done { background: #DDF4EA; color: #14694A; border-radius: 12px; padding: .8rem 1rem; font-weight: 500; margin: .5rem 0 1rem; }

/* sidebar */
.brand { display: flex; align-items: center; gap: .6rem; font-weight: 600; font-size: 1.05rem; color: #14213D; margin-bottom: 1.2rem; }
.logo { display: inline-flex; align-items: center; justify-content: center; width: 1.9rem; height: 1.9rem;
  border-radius: 8px; background: #2F5BEA; color: #FFFFFF; font-weight: 600; }
.ring-wrap { display: flex; align-items: center; gap: .9rem; margin-bottom: 1.1rem; }
.ring { position: relative; width: 64px; height: 64px; border-radius: 50%; display: grid; place-items: center; flex: none; }
.ring::before { content: ""; position: absolute; inset: 8px; background: #FFFFFF; border-radius: 50%; }
.ring span { position: relative; font-weight: 600; font-size: .85rem; color: #14213D; }
.ring-cap { font-size: .85rem; color: #5B6B86; line-height: 1.4; }
.ring-cap b { color: #14213D; font-weight: 600; }
.skill { background: #FFFFFF; border: 1px solid #E3E8F2; border-radius: 12px; padding: .7rem .85rem; margin-bottom: .55rem; }
.srow { display: flex; justify-content: space-between; align-items: baseline; gap: .5rem; }
.sname { font-size: .9rem; font-weight: 500; color: #14213D; }
.tag { font-size: .74rem; font-weight: 500; padding: .1rem .55rem; border-radius: 999px; white-space: nowrap; }
.tag.mastered { background: #DDF4EA; color: #14694A; }
.tag.progress { background: #E3EBFF; color: #1F3FA8; }
.tag.weak { background: #FDE5E3; color: #9B2C26; }
.bar { height: 6px; background: #E9EDF6; border-radius: 999px; margin-top: .55rem; overflow: hidden; }
.bar > span { display: block; height: 100%; border-radius: 999px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

if "S" not in st.session_state:
    st.session_state.S = Student()
    st.session_state.history = []     # messages for the model
    st.session_state.ui = []          # what the student sees: (role, text, feedback)
S, H, ui = st.session_state.S, st.session_state.history, st.session_state.ui


def esc(text):
    return html.escape(str(text))


def send(text):
    st.session_state.todo = text
    st.rerun()


todo = st.session_state.get("todo")
if todo:
    ui.append(("user", todo, ""))


def status(score):
    if score >= MASTERED:
        return "Mastered", "mastered", "#1F9D6B"
    if score < 0.4:
        return "Needs work", "weak", "#D9534F"
    return "In progress", "progress", "#2F5BEA"


def skill_row(sk):
    label, cls, color = status(sk["score"])
    pct = int(round(sk["score"] * 100))
    return (f'<div class="skill"><div class="srow"><span class="sname">{esc(sk["name"])}</span>'
            f'<span class="tag {cls}">{label}</span></div>'
            f'<div class="bar"><span style="width:{pct}%;background:{color}"></span></div></div>')


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown('<div class="brand"><span class="logo">A</span>Adaptive tutor</div>', unsafe_allow_html=True)
    if S.skills:
        overall = int(round(100 * sum(v["score"] for v in S.skills.values()) / len(S.skills)))
        st.markdown(
            f'<div class="ring-wrap"><div class="ring" style="background:conic-gradient(#2F5BEA {overall}%, #E6EAF3 0)">'
            f'<span>{overall}%</span></div><div class="ring-cap"><b>Overall mastery</b><br>{esc(S.topic)}</div></div>',
            unsafe_allow_html=True)
        st.markdown("".join(skill_row(v) for v in S.skills.values()), unsafe_allow_html=True)
    else:
        st.caption("Your skills will appear here once you pick a topic.")
    st.divider()
    st.caption(f"Questions checked: {S.stats['accepted']} accepted, {S.stats['rejected']} rejected")
    target = S.pending or (S.last_graded.get("q", {}).get("id") if S.last_graded else "")
    if target and st.button("Report this question as wrong"):
        S.flagged.add(target)
        st.toast("Thanks, the question is flagged.")
    with st.expander("Agent log (for your report)"):
        for e in S.log[-15:]:
            st.json(e, expanded=False)
    if st.button("Start over"):
        st.session_state.clear()
        st.rerun()

# ---------------------------------------------------------------- header / start screen
if S.topic:
    st.markdown(f'<h1 class="h1">{esc(S.topic)}</h1>'
                '<p class="sub">Answer each question and the tutor adjusts to what you find hard.</p>',
                unsafe_allow_html=True)
elif not ui:
    st.markdown(
        '<h1 class="h1">What do you want to learn?</h1>'
        '<p class="sub">Pick any topic. The tutor builds a skill map, checks where you stand, '
        'then practises what you find hardest.</p>'
        '<div class="steps">'
        '<div class="step"><span class="n">1</span>Pick a topic</div>'
        '<div class="step"><span class="n">2</span>Take a quick check</div>'
        '<div class="step"><span class="n">3</span>Practise your weak spots</div></div>',
        unsafe_allow_html=True)
    cols = st.columns(2)
    for i, t in enumerate(STARTERS):
        if cols[i % 2].button(t, key=f"start_{i}"):
            send(t)
    st.caption("Or type your own topic below.")

# ---------------------------------------------------------------- chat history
for item in ui:
    role, text, *rest = item
    kind = rest[0] if rest else ""
    with st.chat_message(role):
        if kind in ("good", "bad"):
            st.markdown(f'<span class="fb {kind}">{"Correct" if kind == "good" else "Not quite"}</span>',
                        unsafe_allow_html=True)
        if text:
            st.write(text)

# ---------------------------------------------------------------- run the tutor (after the page has drawn)
if todo:
    st.session_state.pop("todo", None)
    try:
        with st.spinner("Thinking..."):
            reply = agent.run_turn(S, H, todo)
    except Exception as e:
        reply = f"Something went wrong: {e}"
    if reply:
        ui.append(("assistant", reply, ""))
    st.rerun()

letter_picked = st.session_state.pop("answer", None)
if letter_picked:
    try:
        with st.spinner("Checking..."):
            result, reply = agent.on_answer(S, H, letter_picked)
        if "error" not in result:
            ui.append(("assistant", reply, "good" if result["correct"] else "bad"))
    except Exception as e:
        ui.append(("assistant", f"Something went wrong: {e}", ""))
    st.rerun()

# ---------------------------------------------------------------- question card
q = S.questions.get(S.pending) if S.pending else None
if q:
    with st.container(border=True):
        level = LEVELS.get(q.get("difficulty"), "Medium")
        st.markdown(f'<div class="chips"><span class="chip">{esc(S.skills[q["skill"]]["name"])}</span>'
                    f'<span class="chip">{level}</span></div><div class="q">{esc(q["question"])}</div>',
                    unsafe_allow_html=True)
        cols = st.columns(2)
        for i, (letter, text) in enumerate(q["options"].items()):
            if cols[i % 2].button(f"{letter}.  {text}", key=f"{q['id']}_{letter}"):
                st.session_state.answer = letter
                st.rerun()
elif S.all_mastered():
    st.markdown('<div class="done">You have mastered every skill in this topic.</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------- free text
if text := st.chat_input("Type a topic or ask a question"):
    send(text)