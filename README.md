# Adaptive AI Learning Agent

An AI tutor that can teach any topic. The student types a topic, the AI splits it into smaller skills, and the tutor asks questions, marks the answers, and focuses on the skills the student is weakest at. If a student keeps failing a skill, it goes back to the skill that comes before it.

## Files
- `llm.py`: the only file that talks to the AI model (OpenAI)
- `state.py`: student scores and the rule for choosing the next skill
- `tools.py`: skill list, question making and checking, marking, explanations
- `agent.py`: the agent loop (the AI picks the next step and the program runs it)
- `app.py`: the Streamlit web page
- `simulate.py`: fake students for testing (makes real API calls, so it costs money)

## How to run (Windows PowerShell)
```
pip install -r requirements.txt
$env:OPENAI_API_KEY="your-key"
python -m streamlit run app.py
```
Optional: `$env:LLM_MODEL="gpt-4o-mini"` to choose the model (this is the default).
Never put your key in the code or push it to GitHub.

To run the fake-student test: `python simulate.py`. Start with a small number of sessions, because each one makes many API calls.

## How we keep the answers correct
- The AI never sees the answer key, and the program marks the answers, not the AI.
- Answer options are shuffled by the program.
- A new question is only used if a separate AI call, which does not see the key, picks the right answer 3 times.
- The agent stops after 6 steps in one turn.
- The student can report a question as wrong.

## Known limits
- The checker lowers the number of wrong questions but cannot remove them, so we check about 50 questions by hand and report the error rate for each topic.
- Question quality is worse for unusual topics.
- The tutor can ask many questions in a row about the same weak skill.