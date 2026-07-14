"""
Agent 1: Resume Intelligence Agent

Parses resume text, extracts skills/experience via LLM-based semantic
analysis (standing in for the BERT/NER pipeline in the original spec),
computes an ATS-style score, and identifies gaps against a target role.
"""
from core.llm_client import ask_json

SYSTEM = """You are the Resume Intelligence Agent inside InterviewGPT Pro.
You analyze resumes with the rigor of an experienced technical recruiter
and ATS (Applicant Tracking System) auditor. Be specific and evidence-based:
every claim should trace back to something actually in the resume text."""


def analyze_resume(resume_text: str, target_role: str) -> dict:
    """
    Returns a structured analysis:
    {
      ats_score: 0-100,
      extracted_skills: [...],
      missing_skills: [...],
      experience_summary: str,
      strengths: [...],
      weaknesses: [...],
      role_match_score: 0-100,
      notes: str
    }
    """
    user = f"""Target role: {target_role}

Resume text:
---
{resume_text[:12000]}
---

Analyze this resume for the target role above. Return JSON with exactly
these keys:
- "ats_score": integer 0-100 (formatting, keyword coverage, clarity)
- "extracted_skills": list of skill strings found in the resume
- "missing_skills": list of skills commonly expected for this role that
  are NOT evidenced in the resume
- "experience_summary": 2-3 sentence summary of the candidate's experience
- "strengths": list of 3-5 short strength statements
- "weaknesses": list of 3-5 short weakness/gap statements
- "role_match_score": integer 0-100, how well this resume matches the target role
- "notes": one paragraph of recruiter-style commentary
"""
    return ask_json(SYSTEM, user)
