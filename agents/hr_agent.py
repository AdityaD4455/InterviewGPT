"""
Agent 4: HR & Behavioral Interview Agent

Asks behavioral questions and evaluates answers against the STAR method,
plus communication clarity and cultural-fit signals.
"""
from core.llm_client import ask_json
from core.rag import retrieve

SYSTEM = """You are the HR & Behavioral Interview Agent inside InterviewGPT Pro.
You evaluate answers using the STAR framework (Situation, Task, Action,
Result) the way a trained HR interviewer would, and you give honest,
specific feedback rather than generic encouragement."""


def generate_behavioral_question(theme: str, history: list) -> dict:
    kb_context = retrieve(f"behavioral interview {theme} STAR", k=2)
    kb_text = "\n\n".join(f"[{c['source']}] {c['text']}" for c in kb_context)
    asked = [h["question"] for h in history]

    user = f"""Theme to probe: {theme}
Already asked in this session (don't repeat): {asked}

Relevant framework notes:
{kb_text}

Generate one behavioral interview question targeting this theme. Return
JSON with:
- "question": the question text
- "theme": echo back the theme
"""
    return ask_json(SYSTEM, user)


def evaluate_star_answer(question: str, answer: str) -> dict:
    user = f"""Question: {question}

Candidate's answer:
---
{answer}
---

Evaluate using the STAR method. Return JSON with:
- "star_coverage": object with boolean keys "situation", "task", "action", "result"
- "score": integer 0-10
- "communication_score": integer 0-10 (clarity, structure, conciseness)
- "feedback": 2-3 sentences of specific, constructive feedback
- "red_flags": list of any red flags noticed (vague ownership, no result, etc.), can be empty
"""
    return ask_json(SYSTEM, user)
