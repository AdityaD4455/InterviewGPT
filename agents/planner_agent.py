"""
Agent 2: Interview Planner Agent

Builds an interview strategy (round order, topic mix, starting difficulty)
based on the resume analysis, target role, company type, and the
candidate's prior session history (long-term memory).
"""
from core.llm_client import ask_json
from core.rag import retrieve

SYSTEM = """You are the Interview Planner Agent inside InterviewGPT Pro.
You design a realistic, personalized interview strategy the way a senior
hiring manager would structure a real interview loop."""


def build_plan(resume_analysis: dict, target_role: str, company_type: str, past_weak_topics: list) -> dict:
    kb_context = retrieve(f"{company_type} interview rounds {target_role}", k=3)
    kb_text = "\n\n".join(f"[{c['source']}] {c['text']}" for c in kb_context)

    user = f"""Target role: {target_role}
Company type: {company_type}
Candidate's previously identified weak topics (may be empty): {past_weak_topics}

Resume analysis:
{resume_analysis}

Relevant knowledge base context:
{kb_text}

Design an interview plan. Return JSON with exactly these keys:
- "rounds": ordered list of objects, each with "round_name" (e.g.
  "Technical - DSA", "Technical - System Design", "HR & Behavioral"),
  "focus_topics" (list), and "starting_difficulty" (one of "easy",
  "medium", "hard")
- "rationale": short paragraph explaining why this plan fits the
  candidate and company type, explicitly referencing at least one
  weak topic or resume gap if relevant
- "estimated_duration_minutes": integer
"""
    return ask_json(SYSTEM, user)
