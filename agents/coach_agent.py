"""
Agent 8: Personalized Career Coach Agent

Turns the gap analysis + full session history into a concrete weekly
learning roadmap and daily task list, tailored to the target role and
company type.
"""
from core.llm_client import ask_json

SYSTEM = """You are the Personalized Career Coach Agent inside InterviewGPT Pro.
You turn diagnosis into a concrete, realistic plan -- specific enough that
the candidate could start today, not generic "practice more" advice."""


def build_roadmap(target_role: str, company_type: str, weak_topics: list,
                   readiness_score: int, weeks: int = 4) -> dict:
    user = f"""Target role: {target_role}
Company type: {company_type}
Current readiness score: {readiness_score}/100
Weak topics accumulated across sessions: {weak_topics}
Plan length: {weeks} weeks

Build a personalized preparation roadmap. Return JSON with:
- "weekly_plan": list of {weeks} objects, each with "week" (int), "focus"
  (short theme), and "goals" (list of 3-5 concrete, specific goals for
  that week -- tie them to the weak topics given)
- "daily_task_template": list of 5-7 short daily task strings a candidate
  could rotate through
- "expected_readiness_after_plan": integer 0-100, realistic projected
  readiness score if the plan is followed
- "summary": 2-3 sentence coach-style motivational but honest summary
"""
    return ask_json(SYSTEM, user)
