"""
Agent 3: Technical Interview Agent

Runs an adaptive technical interview loop: asks a question, evaluates the
candidate's answer, adjusts difficulty up/down, decides whether to ask a
follow-up or move topics, and can generate a hint on request.

State (current_difficulty, topic, history) is held by the caller (the
Streamlit session) and passed in each turn — this agent is stateless,
which keeps it easy to test and to swap into a different orchestrator.
"""
from core.llm_client import ask_json, ask_text
from core.rag import retrieve

SYSTEM = """You are the Technical Interview Agent inside InterviewGPT Pro.
You conduct DSA, ML, and System Design interviews exactly like a sharp
but fair senior engineer running a real interview loop: you ask one
question at a time, you probe reasoning (not just final answers), and you
adapt difficulty based on how the candidate is doing."""


def generate_question(topic: str, difficulty: str, resume_analysis: dict, history: list) -> dict:
    kb_context = retrieve(f"{topic} interview question {difficulty}", k=3)
    kb_text = "\n\n".join(f"[{c['source']}] {c['text']}" for c in kb_context)
    history_text = "\n".join(f"Q: {h['question']}\nA: {h['answer']}\nScore: {h.get('score','?')}" for h in history[-4:])

    user = f"""Topic: {topic}
Difficulty: {difficulty}
Candidate background: {resume_analysis.get('experience_summary', 'N/A')}
Candidate's known skills: {resume_analysis.get('extracted_skills', [])}

Recent Q&A history in this session:
{history_text or '(none yet - this is the first question)'}

Relevant prep material:
{kb_text}

Generate the NEXT interview question. It should follow logically from the
history (a natural follow-up, or a new sub-topic if the last one is
sufficiently covered) and match the given difficulty. Return JSON with:
- "question": the question text
- "topic": the specific sub-topic (e.g. "sliding window", "CAP theorem")
- "difficulty": echo back the difficulty
- "what_a_strong_answer_covers": short list of key points a strong answer would hit
"""
    return ask_json(SYSTEM, user)


def generate_coding_question(difficulty: str, resume_analysis: dict, history: list) -> dict:
    """
    Like generate_question, but specifically for DSA coding problems that
    can be executed and checked against test cases (see core/code_executor.py).
    """
    kb_context = retrieve(f"DSA coding problem {difficulty}", k=3)
    kb_text = "\n\n".join(f"[{c['source']}] {c['text']}" for c in kb_context)
    history_text = "\n".join(f"Q: {h['question']}\nScore: {h.get('score','?')}" for h in history[-4:])

    user = f"""Difficulty: {difficulty}
Candidate's known skills: {resume_analysis.get('extracted_skills', [])}

Recent coding questions already asked this session (don't repeat):
{history_text or '(none yet)'}

Relevant prep material:
{kb_text}

Generate ONE self-contained Python coding interview question with an
auto-gradable function signature. Return JSON with exactly these keys:
- "question": full problem statement (include constraints, e.g. array size)
- "entry_point": the exact function name the candidate must define, e.g. "solve"
- "starter_code": a Python function stub, e.g. "def solve(nums, target):\\n    pass"
- "test_cases": list of 4-6 objects, each {{"input": <value or list of
  positional args>, "expected": <expected return value>}}. If the function
  takes multiple arguments, "input" MUST be a JSON list of those arguments
  in order. Include at least one edge case.
- "difficulty": echo back the difficulty
"""
    return ask_json(SYSTEM, user)


def evaluate_code_solution(question: dict, code: str, execution_result: dict) -> dict:
    """
    Combines objective test-case results (from code_executor) with an LLM
    review of code quality/complexity for a fuller evaluation than
    pass/fail alone.
    """
    results = execution_result.get("results", [])
    passed = sum(1 for r in results if r.get("passed"))
    total = len(results) or 1

    user = f"""Problem: {question['question']}

Candidate's code:
---
{code}
---

Automated test results: {passed}/{total} test cases passed.
Details: {results}
Execution error (if any): {execution_result.get('error')}

Evaluate this submission. Return JSON with:
- "score": integer 0-10 (weight test pass rate heavily, but also code
  quality, readability, and whether complexity is reasonable)
- "feedback": 2-3 sentences of specific, constructive feedback
- "time_complexity_assessment": your read on the time complexity of their approach
- "next_difficulty": one of "easier", "same", "harder"
"""
    evaluation = ask_json(SYSTEM, user)
    evaluation["tests_passed"] = passed
    evaluation["tests_total"] = total
    return evaluation


def evaluate_answer(question: dict, answer: str) -> dict:
    user = f"""Question asked: {question['question']}
Expected strong-answer points: {question.get('what_a_strong_answer_covers', [])}

Candidate's answer:
---
{answer}
---

Evaluate the answer. Return JSON with:
- "score": integer 0-10
- "feedback": 2-3 sentences of specific, constructive feedback
- "correct_points": list of things the candidate got right
- "gaps": list of things missing or wrong
- "next_difficulty": one of "easier", "same", "harder" - recommend based
  on how strong this answer was
- "follow_up_suggested": true/false - whether a follow-up on this same
  question would be more useful than moving to a new topic
"""
    return ask_json(SYSTEM, user)


def generate_hint(question: dict, answer_so_far: str) -> str:
    user = f"""Question: {question['question']}
Candidate's partial/struggling answer: {answer_so_far or '(candidate is stuck, no attempt yet)'}

Give ONE short, Socratic hint (1-2 sentences) that nudges the candidate
toward the right approach WITHOUT giving away the solution."""
    return ask_text(SYSTEM, user, max_tokens=200)
