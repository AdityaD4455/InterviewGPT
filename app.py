diff --git a/app.py b/app.py
index 9c6af77..b34e6e8 100644
--- a/app.py
+++ b/app.py
@@ -12,10 +12,11 @@ from pypdf import PdfReader
 import io
 from streamlit_mic_recorder import mic_recorder
 
-from core import memory, voice_client, code_executor
+from core import memory, voice_client, code_executor, ui
 from agents import resume_agent, planner_agent, technical_agent, hr_agent, gap_agent, coach_agent
 
-st.set_page_config(page_title="InterviewGPT Pro", layout="wide")
+st.set_page_config(page_title="InterviewGPT Pro", layout="wide", page_icon="🎯")
+ui.inject_global_css()
 
 # ---------------------------------------------------------------- session state
 def init_state():
@@ -44,8 +45,14 @@ def init_state():
 init_state()
 
 # ---------------------------------------------------------------- sidebar
-st.sidebar.title("🎯 InterviewGPT Pro")
-st.sidebar.caption("Multi-Agent AI Career Coach")
+with st.sidebar:
+    st.markdown(
+        '<div class="ig-hero" style="padding-bottom:0;">'
+        '<span class="ig-hero-icon" style="font-size:28px;">🎯</span>'
+        '<div><p class="ig-hero-title" style="font-size:1.3rem;">InterviewGPT Pro</p>'
+        '<div class="ig-hero-subtitle">Multi-Agent AI Career Coach</div></div></div>',
+        unsafe_allow_html=True,
+    )
 
 candidate_name = st.sidebar.text_input("Candidate name", value="Demo Candidate")
 candidate_id = st.sidebar.text_input("Candidate ID (used for memory)", value="demo_candidate_1")
@@ -71,11 +78,14 @@ st.session_state.panel_mode = st.sidebar.checkbox(
          "questions within the same live session instead of separate rounds.",
 )
 
-page = st.sidebar.radio(
-    "Workflow",
-    ["1. Resume Analysis", "2. Interview Plan", "3. Live Interview",
-     "4. Gap Report & Roadmap", "5. Dashboard", "6. Leaderboard"],
-)
+WORKFLOW_PAGES = [
+    "1. Resume Analysis", "2. Interview Plan", "3. Live Interview",
+    "4. Gap Report & Roadmap", "5. Dashboard", "6. Leaderboard",
+]
+page = st.sidebar.radio("Workflow", WORKFLOW_PAGES)
+
+_step_labels = ["Resume", "Plan", "Interview", "Gaps", "Dashboard", "Leaderboard"]
+ui.stepper(_step_labels, current_index=WORKFLOW_PAGES.index(page))
 
 st.sidebar.divider()
 st.sidebar.caption(
@@ -87,7 +97,7 @@ st.sidebar.caption(
 
 # ---------------------------------------------------------------- Page 1: Resume Analysis
 if page == "1. Resume Analysis":
-    st.header("Agent 1 — Resume Intelligence")
+    ui.page_header("📄", "Agent 1 — Resume Intelligence", "Parse, score, and benchmark a resume against your target role.")
     uploaded = st.file_uploader("Upload resume (PDF or paste text below)", type=["pdf"])
     pasted = st.text_area("...or paste resume text", height=200)
 
@@ -107,23 +117,28 @@ if page == "1. Resume Analysis":
 
     analysis = st.session_state.resume_analysis
     if analysis:
-        c1, c2 = st.columns(2)
-        c1.metric("ATS Score", f"{analysis.get('ats_score', '?')}/100")
-        c2.metric("Role Match Score", f"{analysis.get('role_match_score', '?')}/100")
-
+        r1, r2, _sp = st.columns([1, 1, 3])
+        with r1:
+            ui.score_ring("ATS Score", analysis.get("ats_score", 0), 100)
+        with r2:
+            ui.score_ring("Role Match", analysis.get("role_match_score", 0), 100)
+        if (analysis.get("ats_score") or 0) >= 85 and (analysis.get("role_match_score") or 0) >= 85:
+            st.balloons()
+
+        ui.divider_glow()
         st.subheader("Experience Summary")
         st.write(analysis.get("experience_summary", ""))
 
         c1, c2 = st.columns(2)
         with c1:
             st.subheader("✅ Extracted Skills")
-            st.write(", ".join(analysis.get("extracted_skills", [])) or "—")
+            ui.chip_row(analysis.get("extracted_skills", []), tone="good")
             st.subheader("💪 Strengths")
             for s in analysis.get("strengths", []):
                 st.markdown(f"- {s}")
         with c2:
             st.subheader("⚠️ Missing Skills for Role")
-            st.write(", ".join(analysis.get("missing_skills", [])) or "—")
+            ui.chip_row(analysis.get("missing_skills", []), tone="bad")
             st.subheader("🔧 Weaknesses")
             for w in analysis.get("weaknesses", []):
                 st.markdown(f"- {w}")
@@ -133,7 +148,7 @@ if page == "1. Resume Analysis":
 
 # ---------------------------------------------------------------- Page 2: Interview Plan
 elif page == "2. Interview Plan":
-    st.header("Agent 2 — Interview Planner")
+    ui.page_header("🗺️", "Agent 2 — Interview Planner", "Design a multi-round strategy tailored to the role and company type.")
     if not st.session_state.resume_analysis:
         st.warning("Run Resume Analysis first (Step 1).")
     else:
@@ -155,12 +170,12 @@ elif page == "2. Interview Plan":
                     f"**{marker}Round {i+1}: {r['round_name']}** "
                     f"(starting difficulty: {r['starting_difficulty']})"
                 )
-                st.caption("Focus topics: " + ", ".join(r.get("focus_topics", [])))
+                ui.chip_row(r.get("focus_topics", []), tone="neutral")
             st.success("Plan ready. Head to '3. Live Interview' to begin.")
 
 # ---------------------------------------------------------------- Page 3: Live Interview
 elif page == "3. Live Interview":
-    st.header("Agents 3 & 4 — Live Adaptive Interview")
+    ui.page_header("🎤", "Agents 3 & 4 — Live Adaptive Interview", "Difficulty adapts to your answers in real time.")
     if st.session_state.panel_mode:
         st.caption("🎭 Panel Interview Mode: Technical and HR agents alternate questions, like a real onsite panel loop.")
     if not st.session_state.plan:
@@ -184,8 +199,13 @@ elif page == "3. Live Interview":
                 use_technical = is_technical_round
 
             st.subheader(f"Round {idx+1}/{len(rounds)}: {current_round['round_name']}")
-            st.caption(f"Difficulty: {st.session_state.current_difficulty}"
-                       + (f" | This turn: {'Technical' if use_technical else 'HR'} agent" if st.session_state.panel_mode else ""))
+            st.progress((idx) / max(len(rounds), 1))
+            diff_tone = {"easy": "good", "medium": "neutral", "hard": "bad"}.get(st.session_state.current_difficulty, "neutral")
+            ui.chip_row(
+                [st.session_state.current_difficulty]
+                + ([f"{'Technical' if use_technical else 'HR'} agent"] if st.session_state.panel_mode else []),
+                tone=diff_tone,
+            )
 
             # ---------------- CODING SUB-FLOW (DSA rounds only, not panel mode) ----------------
             if is_coding_round:
@@ -351,7 +371,7 @@ elif page == "3. Live Interview":
 
 # ---------------------------------------------------------------- Page 4: Gap Report & Roadmap
 elif page == "4. Gap Report & Roadmap":
-    st.header("Agents 7 & 8 — Knowledge Gaps & Career Roadmap")
+    ui.page_header("🧭", "Agents 7 & 8 — Knowledge Gaps & Career Roadmap", "See where you stand, then get a personalized plan to close the gap.")
     transcript = st.session_state.interview_transcript
     if not transcript:
         st.warning("Complete at least part of an interview first (Step 3).")
@@ -370,12 +390,27 @@ elif page == "4. Gap Report & Roadmap":
 
         gaps = st.session_state.gap_analysis
         if gaps:
-            c1, c2 = st.columns(2)
-            c1.metric("Readiness Score", f"{gaps.get('readiness_score','?')}/100")
-            c2.metric("Confidence Trend", gaps.get("confidence_trend", "?"))
+            r1, r2, _sp = st.columns([1, 1, 3])
+            with r1:
+                ui.score_ring("Readiness", gaps.get("readiness_score", 0), 100)
+            with r2:
+                st.markdown(
+                    f'<div style="height:112px;display:flex;flex-direction:column;justify-content:center;">'
+                    f'<div style="font-size:0.78rem;color:rgba(120,120,140,0.9);font-weight:600;">Confidence Trend</div>'
+                    f'<div style="font-size:1.6rem;font-weight:800;">{gaps.get("confidence_trend", "?")}</div>'
+                    f"</div>",
+                    unsafe_allow_html=True,
+                )
+            if (gaps.get("readiness_score") or 0) >= 80:
+                st.balloons()
 
+            ui.divider_glow()
             st.subheader("Weak Topics")
-            st.write(", ".join(gaps.get("weak_topics", [])) or "None identified 🎉")
+            weak = gaps.get("weak_topics", [])
+            if weak:
+                ui.chip_row(weak, tone="bad")
+            else:
+                st.success("None identified 🎉")
 
             st.subheader("Failure Risk Areas")
             for f in gaps.get("failure_risk_areas", []):
@@ -411,7 +446,7 @@ elif page == "4. Gap Report & Roadmap":
 
 # ---------------------------------------------------------------- Page 5: Dashboard
 elif page == "5. Dashboard":
-    st.header("📊 AI Career Report Dashboard")
+    ui.page_header("📊", "AI Career Report Dashboard", "Track progress across every saved session.")
     history = memory.get_session_history(candidate_id) if candidate_id else []
     if not history:
         st.info("No saved sessions yet for this candidate ID.")
@@ -419,10 +454,19 @@ elif page == "5. Dashboard":
         for i, s in enumerate(history):
             st.subheader(f"Session {i+1} — {s['session_type']}")
             c1, c2 = st.columns(2)
-            c1.metric("Avg Score", f"{s['scores'].get('avg_score', 0):.1f}/10")
-            c2.metric("Questions Answered", s['scores'].get('n_questions', 0))
-            st.caption("Weak topics: " + (", ".join(s["weak_topics"]) or "none"))
-            st.divider()
+            with c1:
+                ui.score_ring("Avg Score", round(s["scores"].get("avg_score", 0), 1), 10, size=96)
+            with c2:
+                st.markdown(
+                    f'<div style="height:96px;display:flex;flex-direction:column;justify-content:center;">'
+                    f'<div style="font-size:0.78rem;color:rgba(120,120,140,0.9);font-weight:600;">Questions Answered</div>'
+                    f'<div style="font-size:1.8rem;font-weight:800;">{s["scores"].get("n_questions", 0)}</div>'
+                    f"</div>",
+                    unsafe_allow_html=True,
+                )
+            st.caption("Weak topics:")
+            ui.chip_row(s["weak_topics"], tone="bad") if s["weak_topics"] else st.caption("none")
+            ui.divider_glow()
 
         all_weak = memory.get_all_weak_topics(candidate_id)
         if all_weak:
@@ -433,7 +477,7 @@ elif page == "5. Dashboard":
 
 # ---------------------------------------------------------------- Page 6: Leaderboard
 elif page == "6. Leaderboard":
-    st.header("🏆 Multi-Candidate Leaderboard")
+    ui.page_header("🏆", "Multi-Candidate Leaderboard", "Ranked by average interview score across all saved sessions.")
     st.caption("Ranks every candidate who has completed at least one saved session, by average interview score.")
     board = memory.get_leaderboard()
     if not board:
