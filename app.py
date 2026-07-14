"""
InterviewGPT Pro - Main Application

A Streamlit UI that orchestrates the agents:
  Resume Intelligence -> Interview Planner -> Technical/HR Interview
  -> Knowledge Gap Detection -> Career Coach

Run with:  streamlit run app.py
"""
import streamlit as st
from pypdf import PdfReader
import io
from streamlit_mic_recorder import mic_recorder

from core import memory, voice_client, code_executor
from agents import resume_agent, planner_agent, technical_agent, hr_agent, gap_agent, coach_agent

st.set_page_config(page_title="InterviewGPT Pro", layout="wide")

# ---------------------------------------------------------------- session state
def init_state():
    defaults = {
        "candidate_id": "",
        "resume_text": "",
        "resume_analysis": None,
        "plan": None,
        "interview_transcript": [],
        "current_round_idx": 0,
        "current_difficulty": "medium",
        "current_question": None,
        "gap_analysis": None,
        "roadmap": None,
        "voice_draft_answer": "",
        "last_audio_id": None,
        "current_code_question": None,
        "last_run_result": None,
        "panel_mode": False,
        "voice_version": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ---------------------------------------------------------------- sidebar
st.sidebar.title("🎯 InterviewGPT Pro")
st.sidebar.caption("Multi-Agent AI Career Coach")

candidate_name = st.sidebar.text_input("Candidate name", value="Demo Candidate")
candidate_id = st.sidebar.text_input("Candidate ID (used for memory)", value="demo_candidate_1")
target_role = st.sidebar.text_input("Target role", value="Backend Software Engineer")
company_type = st.sidebar.selectbox(
    "Company type",
    ["Big Tech (FAANG-style)", "High-Growth Startup", "Product-Based Mid-Size", "Service-Based / Consulting"],
)

if candidate_id:
    memory.upsert_candidate(candidate_id, candidate_name)
    st.session_state.candidate_id = candidate_id

past_weak_topics = memory.get_all_weak_topics(candidate_id) if candidate_id else []
if past_weak_topics:
    st.sidebar.markdown("**Known weak topics (from memory):**")
    st.sidebar.caption(", ".join(sorted(set(past_weak_topics))))

st.session_state.panel_mode = st.sidebar.checkbox(
    "🎭 Panel Interview Mode",
    value=st.session_state.panel_mode,
    help="Simulates a real onsite panel: Technical and HR agents alternate "
         "questions within the same live session instead of separate rounds.",
)

page = st.sidebar.radio(
    "Workflow",
    ["1. Resume Analysis", "2. Interview Plan", "3. Live Interview",
     "4. Gap Report & Roadmap", "5. Dashboard", "6. Leaderboard"],
)

st.sidebar.divider()
st.sidebar.caption(
    "Note: Facial-emotion analysis from the original spec requires live "
    "webcam capture + CV models and is out of scope for this local "
    "prototype. Voice input is now live (Groq Whisper). See README for "
    "how to extend into facial-emotion tracking."
)

# ---------------------------------------------------------------- Page 1: Resume Analysis
if page == "1. Resume Analysis":
    st.header("Agent 1 — Resume Intelligence")
    uploaded = st.file_uploader("Upload resume (PDF or paste text below)", type=["pdf"])
    pasted = st.text_area("...or paste resume text", height=200)

    resume_text = ""
    if uploaded is not None:
        reader = PdfReader(io.BytesIO(uploaded.read()))
        resume_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    elif pasted:
        resume_text = pasted

    if st.button("Analyze Resume", type="primary", disabled=not resume_text):
        with st.spinner("Parsing resume, extracting skills, scoring ATS fit..."):
            analysis = resume_agent.analyze_resume(resume_text, target_role)
            st.session_state.resume_text = resume_text
            st.session_state.resume_analysis = analysis
            memory.save_resume_analysis(candidate_id, target_role, analysis)

    analysis = st.session_state.resume_analysis
    if analysis:
        c1, c2 = st.columns(2)
        c1.metric("ATS Score", f"{analysis.get('ats_score', '?')}/100")
        c2.metric("Role Match Score", f"{analysis.get('role_match_score', '?')}/100")

        st.subheader("Experience Summary")
        st.write(analysis.get("experience_summary", ""))

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("✅ Extracted Skills")
            st.write(", ".join(analysis.get("extracted_skills", [])) or "—")
            st.subheader("💪 Strengths")
            for s in analysis.get("strengths", []):
                st.markdown(f"- {s}")
        with c2:
            st.subheader("⚠️ Missing Skills for Role")
            st.write(", ".join(analysis.get("missing_skills", [])) or "—")
            st.subheader("🔧 Weaknesses")
            for w in analysis.get("weaknesses", []):
                st.markdown(f"- {w}")

        st.subheader("Recruiter Notes")
        st.info(analysis.get("notes", ""))

# ---------------------------------------------------------------- Page 2: Interview Plan
elif page == "2. Interview Plan":
    st.header("Agent 2 — Interview Planner")
    if not st.session_state.resume_analysis:
        st.warning("Run Resume Analysis first (Step 1).")
    else:
        if st.button("Generate Interview Plan", type="primary"):
            with st.spinner("Designing interview strategy..."):
                plan = planner_agent.build_plan(
                    st.session_state.resume_analysis, target_role, company_type, past_weak_topics
                )
                st.session_state.plan = plan
                st.session_state.current_round_idx = 0

        plan = st.session_state.plan
        if plan:
            st.info(plan.get("rationale", ""))
            st.caption(f"Estimated duration: {plan.get('estimated_duration_minutes', '?')} minutes")
            for i, r in enumerate(plan.get("rounds", [])):
                marker = "▶️ " if i == st.session_state.current_round_idx else ""
                st.markdown(
                    f"**{marker}Round {i+1}: {r['round_name']}** "
                    f"(starting difficulty: {r['starting_difficulty']})"
                )
                st.caption("Focus topics: " + ", ".join(r.get("focus_topics", [])))
            st.success("Plan ready. Head to '3. Live Interview' to begin.")

# ---------------------------------------------------------------- Page 3: Live Interview
elif page == "3. Live Interview":
    st.header("Agents 3 & 4 — Live Adaptive Interview")
    if st.session_state.panel_mode:
        st.caption("🎭 Panel Interview Mode: Technical and HR agents alternate questions, like a real onsite panel loop.")
    if not st.session_state.plan:
        st.warning("Generate an Interview Plan first (Step 2).")
    else:
        rounds = st.session_state.plan["rounds"]
        idx = st.session_state.current_round_idx
        if idx >= len(rounds):
            st.success("All rounds complete! Go to '4. Gap Report & Roadmap'.")
        else:
            current_round = rounds[idx]
            round_transcript = [t for t in st.session_state.interview_transcript if t.get("round") == idx]
            round_name_lower = current_round["round_name"].lower()
            is_technical_round = any(k in round_name_lower for k in ["technical", "dsa", "system design", "ml"])
            is_coding_round = ("dsa" in round_name_lower or "coding" in round_name_lower) and not st.session_state.panel_mode

            if st.session_state.panel_mode:
                # Alternate agents every question regardless of round labeling
                use_technical = (len(round_transcript) % 2 == 0)
            else:
                use_technical = is_technical_round

            st.subheader(f"Round {idx+1}/{len(rounds)}: {current_round['round_name']}")
            st.caption(f"Difficulty: {st.session_state.current_difficulty}"
                       + (f" | This turn: {'Technical' if use_technical else 'HR'} agent" if st.session_state.panel_mode else ""))

            # ---------------- CODING SUB-FLOW (DSA rounds only, not panel mode) ----------------
            if is_coding_round:
                if st.session_state.current_code_question is None:
                    with st.spinner("Preparing a coding question..."):
                        cq = technical_agent.generate_coding_question(
                            difficulty=st.session_state.current_difficulty,
                            resume_analysis=st.session_state.resume_analysis,
                            history=round_transcript,
                        )
                        st.session_state.current_code_question = cq
                        st.session_state.last_run_result = None

                cq = st.session_state.current_code_question
                st.markdown(f"### 💻 {cq['question']}")
                st.caption(f"Function to implement: `{cq['entry_point']}`")

                code = st.text_area(
                    "Your Python solution",
                    value=cq.get("starter_code", f"def {cq['entry_point']}():\n    pass"),
                    height=250,
                    key=f"code_{idx}_{len(round_transcript)}",
                )

                col1, col2, col3 = st.columns(3)
                if col1.button("▶️ Run Tests"):
                    with st.spinner("Executing your code..."):
                        st.session_state.last_run_result = code_executor.run_python_solution(
                            code, cq["entry_point"], cq["test_cases"]
                        )

                result = st.session_state.last_run_result
                if result:
                    if result["error"] and not result["results"]:
                        st.error(f"Execution error: {result['error']}")
                    else:
                        passed = sum(1 for r in result["results"] if r["passed"])
                        total = len(result["results"])
                        (st.success if passed == total else st.warning)(f"Tests passed: {passed}/{total}")
                        for r in result["results"]:
                            icon = "✅" if r["passed"] else "❌"
                            extra = f" — error: {r['error']}" if r.get("error") else ""
                            st.caption(f"{icon} input={r['input']} expected={r['expected']} got={r.get('actual')}{extra}")

                if col2.button("Submit Solution", type="primary"):
                    with st.spinner("Evaluating..."):
                        exec_result = st.session_state.last_run_result or code_executor.run_python_solution(
                            code, cq["entry_point"], cq["test_cases"]
                        )
                        eval_result = technical_agent.evaluate_code_solution(cq, code, exec_result)
                        entry = {
                            "round": idx, "agent": "technical-coding", "question": cq["question"],
                            "answer": code, "score": eval_result["score"],
                            "feedback": eval_result["feedback"],
                            "tests_passed": f"{eval_result['tests_passed']}/{eval_result['tests_total']}",
                        }
                        diff_map = {"easier": "easy", "same": st.session_state.current_difficulty, "harder": "hard"}
                        st.session_state.current_difficulty = diff_map[eval_result["next_difficulty"]]
                        st.session_state.interview_transcript.append(entry)
                        st.session_state.current_code_question = None
                        st.session_state.last_run_result = None
                        st.rerun()

                if col3.button("Skip to a different question"):
                    st.session_state.current_code_question = None
                    st.session_state.last_run_result = None
                    st.rerun()

            # ---------------- CONCEPTUAL / BEHAVIORAL FLOW ----------------
            else:
                if st.session_state.current_question is None:
                    with st.spinner("Preparing next question..."):
                        if use_technical:
                            q = technical_agent.generate_question(
                                topic=current_round["focus_topics"][0] if current_round["focus_topics"] else "general",
                                difficulty=st.session_state.current_difficulty,
                                resume_analysis=st.session_state.resume_analysis,
                                history=round_transcript,
                            )
                        else:
                            q = hr_agent.generate_behavioral_question(
                                theme=current_round["focus_topics"][0] if current_round["focus_topics"] else "general",
                                history=round_transcript,
                            )
                        st.session_state.current_question = q

                q = st.session_state.current_question
                icon = "🧠" if use_technical else "🗣️"
                st.markdown(f"### {icon} {q['question']}")

                # ---- Voice input (real speech-to-text via Groq Whisper) ----
                st.caption("🎙️ Record your answer out loud, or just type below.")
                audio = mic_recorder(
                    start_prompt="🎙️ Start Recording",
                    stop_prompt="⏹️ Stop & Transcribe",
                    just_once=True,
                    format="webm",
                    key=f"mic_{idx}_{len(round_transcript)}",
                )
                if audio and audio.get("id") != st.session_state.last_audio_id:
                    st.session_state.last_audio_id = audio["id"]
                    with st.spinner("Transcribing your answer..."):
                        try:
                            transcribed = voice_client.transcribe_audio(
                                audio["bytes"], filename=f"answer.{audio.get('format', 'webm')}"
                            )
                            st.session_state.voice_draft_answer = transcribed
                            st.session_state.voice_version += 1
                        except Exception as e:
                            st.error(f"Transcription failed: {e}")
                    st.rerun()

                answer_key = f"answer_{idx}_{len(round_transcript)}_{st.session_state.voice_version}"
                answer = st.text_area(
                    "Your answer (edit the transcribed text if needed)",
                    value=st.session_state.voice_draft_answer,
                    key=answer_key,
                )

                col1, col2, col3 = st.columns(3)
                if col1.button("Submit Answer", type="primary", disabled=not answer):
                    with st.spinner("Evaluating..."):
                        if use_technical:
                            eval_result = technical_agent.evaluate_answer(q, answer)
                            entry = {
                                "round": idx, "agent": "technical", "question": q["question"],
                                "answer": answer, "score": eval_result["score"],
                                "feedback": eval_result["feedback"],
                            }
                            diff_map = {"easier": "easy", "same": st.session_state.current_difficulty, "harder": "hard"}
                            st.session_state.current_difficulty = diff_map[eval_result["next_difficulty"]]
                        else:
                            eval_result = hr_agent.evaluate_star_answer(q["question"], answer)
                            entry = {
                                "round": idx, "agent": "hr", "question": q["question"],
                                "answer": answer, "score": eval_result["score"],
                                "feedback": eval_result["feedback"],
                            }
                        st.session_state.interview_transcript.append(entry)
                        st.session_state.current_question = None
                        st.session_state.voice_draft_answer = ""
                        st.rerun()

                if col2.button("Get a Hint") and use_technical:
                    with st.spinner("Thinking of a nudge..."):
                        hint = technical_agent.generate_hint(q, answer)
                        st.info(f"💡 Hint: {hint}")

                if col3.button("End this round early"):
                    st.session_state.current_round_idx += 1
                    st.session_state.current_question = None
                    st.session_state.voice_draft_answer = ""
                    st.rerun()

        if st.session_state.interview_transcript:
            with st.expander(f"Transcript so far ({len(st.session_state.interview_transcript)} answered)"):
                for t in st.session_state.interview_transcript:
                    st.markdown(f"**[{t['agent']}] Q:** {t['question']}")
                    st.markdown(f"**A:** {t['answer']}")
                    tests_line = f" ({t['tests_passed']} tests passed)" if "tests_passed" in t else ""
                    st.markdown(f"**Score:** {t['score']}/10{tests_line} — {t['feedback']}")
                    st.divider()

# ---------------------------------------------------------------- Page 4: Gap Report & Roadmap
elif page == "4. Gap Report & Roadmap":
    st.header("Agents 7 & 8 — Knowledge Gaps & Career Roadmap")
    transcript = st.session_state.interview_transcript
    if not transcript:
        st.warning("Complete at least part of an interview first (Step 3).")
    else:
        if st.button("Analyze Gaps & Save Session", type="primary"):
            with st.spinner("Detecting knowledge gaps..."):
                scores = {
                    "avg_score": sum(t["score"] for t in transcript) / len(transcript),
                    "n_questions": len(transcript),
                }
                gaps = gap_agent.detect_gaps(transcript, scores)
                st.session_state.gap_analysis = gaps
                memory.save_session(
                    candidate_id, "mixed", transcript, scores, gaps.get("weak_topics", [])
                )

        gaps = st.session_state.gap_analysis
        if gaps:
            c1, c2 = st.columns(2)
            c1.metric("Readiness Score", f"{gaps.get('readiness_score','?')}/100")
            c2.metric("Confidence Trend", gaps.get("confidence_trend", "?"))

            st.subheader("Weak Topics")
            st.write(", ".join(gaps.get("weak_topics", [])) or "None identified 🎉")

            st.subheader("Failure Risk Areas")
            for f in gaps.get("failure_risk_areas", []):
                st.markdown(f"- {f}")

            st.subheader("Recommended Resources (from knowledge base)")
            for topic, resources in gaps.get("recommended_resources", {}).items():
                st.markdown(f"**{topic}**")
                for r in resources:
                    st.caption(f"[{r['source']}] {r['snippet']}...")

            st.divider()
            if st.button("Generate Personalized Roadmap"):
                with st.spinner("Building your roadmap..."):
                    all_weak = memory.get_all_weak_topics(candidate_id)
                    roadmap = coach_agent.build_roadmap(
                        target_role, company_type, all_weak, gaps.get("readiness_score", 50)
                    )
                    st.session_state.roadmap = roadmap
                    memory.save_roadmap(candidate_id, roadmap)

            roadmap = st.session_state.roadmap
            if roadmap:
                st.success(roadmap.get("summary", ""))
                st.caption(f"Projected readiness after plan: {roadmap.get('expected_readiness_after_plan','?')}/100")
                for week in roadmap.get("weekly_plan", []):
                    st.markdown(f"**Week {week['week']}: {week['focus']}**")
                    for g in week.get("goals", []):
                        st.markdown(f"- {g}")
                st.subheader("Daily Task Rotation")
                for t in roadmap.get("daily_task_template", []):
                    st.markdown(f"- {t}")

# ---------------------------------------------------------------- Page 5: Dashboard
elif page == "5. Dashboard":
    st.header("📊 AI Career Report Dashboard")
    history = memory.get_session_history(candidate_id) if candidate_id else []
    if not history:
        st.info("No saved sessions yet for this candidate ID.")
    else:
        for i, s in enumerate(history):
            st.subheader(f"Session {i+1} — {s['session_type']}")
            c1, c2 = st.columns(2)
            c1.metric("Avg Score", f"{s['scores'].get('avg_score', 0):.1f}/10")
            c2.metric("Questions Answered", s['scores'].get('n_questions', 0))
            st.caption("Weak topics: " + (", ".join(s["weak_topics"]) or "none"))
            st.divider()

        all_weak = memory.get_all_weak_topics(candidate_id)
        if all_weak:
            from collections import Counter
            st.subheader("Most Persistent Weak Topics")
            for topic, count in Counter(all_weak).most_common(5):
                st.markdown(f"- **{topic}** (flagged {count}x)")

# ---------------------------------------------------------------- Page 6: Leaderboard
elif page == "6. Leaderboard":
    st.header("🏆 Multi-Candidate Leaderboard")
    st.caption("Ranks every candidate who has completed at least one saved session, by average interview score.")
    board = memory.get_leaderboard()
    if not board:
        st.info("No completed sessions yet across any candidate. Finish an interview and save it (Step 4) to appear here.")
    else:
        import pandas as pd
        df = pd.DataFrame(board)
        df.insert(0, "Rank", range(1, len(df) + 1))
        df = df.rename(columns={
            "candidate_id": "Candidate ID", "name": "Name",
            "sessions_completed": "Sessions", "total_questions": "Total Questions",
            "avg_score": "Avg Score (/10)",
        })
        df = df.drop(columns=["latest_session_at"])
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()
        top = board[0]
        st.success(f"🥇 Top performer: **{top['name']}** ({top['candidate_id']}) — {top['avg_score']}/10 avg across {top['sessions_completed']} session(s)")
