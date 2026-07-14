"""
Long-Term Memory System.

Tracks candidates across multiple sessions: resume analyses, interview
transcripts, scores, weak topics, and roadmap history. Backed by SQLite
so it survives restarts (swap for Postgres in production, same schema).
"""
import sqlite3
import json
import os
import time
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "db", "interviewgpt.sqlite3")


@contextmanager
def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                candidate_id TEXT PRIMARY KEY,
                name TEXT,
                created_at REAL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS resume_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id TEXT,
                target_role TEXT,
                analysis_json TEXT,
                created_at REAL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id TEXT,
                session_type TEXT,
                transcript_json TEXT,
                scores_json TEXT,
                weak_topics_json TEXT,
                created_at REAL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS roadmaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id TEXT,
                roadmap_json TEXT,
                created_at REAL
            )
        """)


def upsert_candidate(candidate_id: str, name: str):
    with _conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO candidates (candidate_id, name, created_at) VALUES (?, ?, ?)",
            (candidate_id, name, time.time()),
        )


def save_resume_analysis(candidate_id: str, target_role: str, analysis: dict):
    with _conn() as c:
        c.execute(
            "INSERT INTO resume_analyses (candidate_id, target_role, analysis_json, created_at) VALUES (?, ?, ?, ?)",
            (candidate_id, target_role, json.dumps(analysis), time.time()),
        )


def get_latest_resume_analysis(candidate_id: str):
    with _conn() as c:
        row = c.execute(
            "SELECT * FROM resume_analyses WHERE candidate_id=? ORDER BY created_at DESC LIMIT 1",
            (candidate_id,),
        ).fetchone()
        return dict(row, analysis=json.loads(row["analysis_json"])) if row else None


def save_session(candidate_id: str, session_type: str, transcript: list, scores: dict, weak_topics: list):
    with _conn() as c:
        c.execute(
            """INSERT INTO sessions
               (candidate_id, session_type, transcript_json, scores_json, weak_topics_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (candidate_id, session_type, json.dumps(transcript), json.dumps(scores),
             json.dumps(weak_topics), time.time()),
        )


def get_session_history(candidate_id: str):
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM sessions WHERE candidate_id=? ORDER BY created_at ASC", (candidate_id,)
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["transcript"] = json.loads(d.pop("transcript_json"))
            d["scores"] = json.loads(d.pop("scores_json"))
            d["weak_topics"] = json.loads(d.pop("weak_topics_json"))
            out.append(d)
        return out


def get_all_weak_topics(candidate_id: str) -> list:
    topics = []
    for s in get_session_history(candidate_id):
        topics.extend(s["weak_topics"])
    return topics


def save_roadmap(candidate_id: str, roadmap: dict):
    with _conn() as c:
        c.execute(
            "INSERT INTO roadmaps (candidate_id, roadmap_json, created_at) VALUES (?, ?, ?)",
            (candidate_id, json.dumps(roadmap), time.time()),
        )


def list_candidates():
    with _conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM candidates ORDER BY created_at DESC").fetchall()]


def get_leaderboard() -> list:
    """
    Aggregate stats per candidate across all their sessions:
    avg score, total questions answered, sessions completed, latest
    readiness signal (best-effort from most recent session's weak topics
    count as a rough proxy). Sorted by avg_score descending.
    """
    candidates = list_candidates()
    leaderboard = []
    for cand in candidates:
        history = get_session_history(cand["candidate_id"])
        if not history:
            continue
        total_q = sum(s["scores"].get("n_questions", 0) for s in history)
        avg_scores = [s["scores"].get("avg_score", 0) for s in history if s["scores"].get("avg_score") is not None]
        overall_avg = sum(avg_scores) / len(avg_scores) if avg_scores else 0
        leaderboard.append({
            "candidate_id": cand["candidate_id"],
            "name": cand["name"],
            "sessions_completed": len(history),
            "total_questions": total_q,
            "avg_score": round(overall_avg, 2),
            "latest_session_at": history[-1]["created_at"],
        })
    leaderboard.sort(key=lambda x: x["avg_score"], reverse=True)
    return leaderboard


init_db()
