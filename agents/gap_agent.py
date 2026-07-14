"""
Agent 7: Knowledge Gap Detection Agent

Analyzes a completed interview transcript (technical + behavioral) to
identify weak topics, estimate a readiness/failure-risk signal, and
recommend specific knowledge base resources to study.

Note: the original spec calls for XGBoost/Random Forest/transformer
classifiers trained on historical pass/fail data. Without a labeled
training set, this agent uses the LLM as a strong zero-shot evaluator
over the transcript instead. Swap in a trained classifier once you have
enough labeled session outcomes (see README "Scaling this up").
"""
from core.llm_client import ask_json
from core.rag import retrieve

SYSTEM = """You are the Knowledge Gap Detection Agent inside InterviewGPT Pro.
You analyze full interview transcripts to identify genuine, specific
knowledge or communication gaps -- not vague generalities."""


def detect_gaps(transcript: list, scores: dict) -> dict:
    transcript_text = "\n\n".join(
        f"[{t.get('agent','?')}] Q: {t['question']}\nA: {t['answer']}\nScore: {t.get('score','?')}/10"
        for t in transcript
    )

    user = f"""Full interview transcript:
{transcript_text}

Aggregate scores so far: {scores}

Analyze this transcript. Return JSON with:
- "weak_topics": list of specific topic strings (e.g. "dynamic programming",
  "system design trade-off articulation", "STAR result quantification")
- "readiness_score": integer 0-100, likelihood this candidate would clear
  a real interview loop like this one
- "failure_risk_areas": list of 2-4 specific areas most likely to cause
  a rejection if unaddressed
- "confidence_trend": one of "improving", "flat", "declining" based on
  how scores moved through the transcript
"""
    result = ask_json(SYSTEM, user)

    # Attach concrete KB resources for each weak topic (real retrieval, not LLM-guessed)
    resources = {}
    for topic in result.get("weak_topics", []):
        hits = retrieve(topic, k=2)
        resources[topic] = [{"source": h["source"], "snippet": h["text"][:200]} for h in hits]
    result["recommended_resources"] = resources
    return result
