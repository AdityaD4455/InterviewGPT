"""
core/ui.py
----------
Small, dependency-free UI layer that makes the Streamlit front-end feel
alive: smooth page/element transitions, animated buttons & cards,
a progress stepper for the workflow, animated score rings, and staggered
skill "chips". Everything is plain CSS (+ a tiny bit of inline SVG) so it
renders reliably through st.markdown(unsafe_allow_html=True) with no extra
pip dependencies and no iframes.

Usage:
    from core import ui
    ui.inject_global_css()          # once, right after st.set_page_config
    ui.page_header("🎯", "Title", "Subtitle")
    ui.stepper(["A", "B", "C"], current_index=1)
    ui.score_ring("ATS Score", 82, 100)
    ui.chip_row(["Python", "SQL"], tone="good")
"""
import uuid
import streamlit as st

# ---------------------------------------------------------------- palette
PRIMARY = "#6C5CE7"
PRIMARY_2 = "#00B4D8"
GOOD = "#10B981"
WARN = "#F59E0B"
BAD = "#EF4444"


def inject_global_css():
    """Inject one global stylesheet that animates & restyles Streamlit's
    built-in widgets. Safe to call once per script run."""
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        :root {{
            --ig-primary: {PRIMARY};
            --ig-primary-2: {PRIMARY_2};
            --ig-good: {GOOD};
            --ig-warn: {WARN};
            --ig-bad: {BAD};
        }}

        /* ---------- page-level entrance animation ---------- */
        @keyframes igFadeUp {{
            from {{ opacity: 0; transform: translateY(14px); }}
            to   {{ opacity: 1; transform: translateY(0); }}
        }}
        section.main > div.block-container {{
            animation: igFadeUp 0.45s cubic-bezier(.2,.8,.2,1) both;
        }}
        div[data-testid="stVerticalBlock"] > div.element-container {{
            animation: igFadeUp 0.4s cubic-bezier(.2,.8,.2,1) both;
        }}
        /* stagger the first ~14 top-level blocks so content cascades in */
        div.block-container > div > div[data-testid="stVerticalBlock"] > div.element-container:nth-child(1) {{ animation-delay: .02s; }}
        div.block-container > div > div[data-testid="stVerticalBlock"] > div.element-container:nth-child(2) {{ animation-delay: .06s; }}
        div.block-container > div > div[data-testid="stVerticalBlock"] > div.element-container:nth-child(3) {{ animation-delay: .10s; }}
        div.block-container > div > div[data-testid="stVerticalBlock"] > div.element-container:nth-child(4) {{ animation-delay: .14s; }}
        div.block-container > div > div[data-testid="stVerticalBlock"] > div.element-container:nth-child(5) {{ animation-delay: .18s; }}
        div.block-container > div > div[data-testid="stVerticalBlock"] > div.element-container:nth-child(6) {{ animation-delay: .22s; }}
        div.block-container > div > div[data-testid="stVerticalBlock"] > div.element-container:nth-child(7) {{ animation-delay: .26s; }}
        div.block-container > div > div[data-testid="stVerticalBlock"] > div.element-container:nth-child(8) {{ animation-delay: .30s; }}

        /* ---------- buttons ---------- */
        .stButton > button, .stDownloadButton > button {{
            border-radius: 10px !important;
            border: 1px solid rgba(108,92,231,0.25) !important;
            transition: transform .18s ease, box-shadow .18s ease, background-color .18s ease, border-color .18s ease !important;
            font-weight: 600 !important;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover {{
            transform: translateY(-2px) scale(1.015);
            box-shadow: 0 8px 20px rgba(108,92,231,0.28);
            border-color: var(--ig-primary) !important;
        }}
        .stButton > button:active {{
            transform: translateY(0) scale(0.98);
            transition-duration: .05s !important;
        }}
        .stButton > button[kind="primary"] {{
            background: linear-gradient(120deg, var(--ig-primary), var(--ig-primary-2)) !important;
            background-size: 160% 160% !important;
            border: none !important;
            animation: igGradientShift 6s ease infinite;
        }}
        .stButton > button[kind="primary"]:hover {{
            box-shadow: 0 10px 26px rgba(108,92,231,0.45);
        }}
        @keyframes igGradientShift {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}

        /* ---------- text inputs / textareas / selects ---------- */
        .stTextInput input, .stTextArea textarea, .stNumberInput input {{
            border-radius: 10px !important;
            transition: box-shadow .2s ease, border-color .2s ease !important;
        }}
        .stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {{
            box-shadow: 0 0 0 3px rgba(108,92,231,0.18) !important;
            border-color: var(--ig-primary) !important;
        }}
        div[data-baseweb="select"] > div {{
            border-radius: 10px !important;
            transition: box-shadow .2s ease, border-color .2s ease !important;
        }}
        div[data-baseweb="select"]:hover > div {{
            border-color: var(--ig-primary) !important;
        }}

        /* ---------- file uploader ---------- */
        [data-testid="stFileUploaderDropzone"] {{
            border-radius: 14px !important;
            transition: border-color .25s ease, background-color .25s ease, transform .2s ease !important;
        }}
        [data-testid="stFileUploaderDropzone"]:hover {{
            border-color: var(--ig-primary) !important;
            background-color: rgba(108,92,231,0.04) !important;
        }}

        /* ---------- metrics ---------- */
        div[data-testid="stMetric"] {{
            background: linear-gradient(180deg, rgba(108,92,231,0.06), rgba(0,180,216,0.03));
            border: 1px solid rgba(108,92,231,0.12);
            border-radius: 14px;
            padding: 14px 16px 10px 16px;
            transition: transform .2s ease, box-shadow .2s ease;
            animation: igFadeUp .5s ease both;
        }}
        div[data-testid="stMetric"]:hover {{
            transform: translateY(-3px);
            box-shadow: 0 10px 24px rgba(108,92,231,0.16);
        }}

        /* ---------- expander ---------- */
        details {{
            border-radius: 12px !important;
            transition: box-shadow .2s ease, border-color .2s ease !important;
        }}
        details:hover {{
            border-color: var(--ig-primary) !important;
        }}
        summary {{
            transition: color .2s ease !important;
        }}

        /* ---------- alerts (info/success/warning/error) ---------- */
        @keyframes igSlideIn {{
            from {{ opacity: 0; transform: translateX(-8px); }}
            to   {{ opacity: 1; transform: translateX(0); }}
        }}
        div[data-testid="stAlert"] {{
            border-radius: 12px !important;
            animation: igSlideIn .35s ease both;
            transition: transform .2s ease;
        }}
        div[data-testid="stAlert"]:hover {{
            transform: translateX(2px);
        }}

        /* ---------- progress bar ---------- */
        .stProgress > div > div > div {{
            background-image: linear-gradient(90deg, var(--ig-primary), var(--ig-primary-2)) !important;
            background-size: 200% 100%;
            animation: igGradientShift 3s ease infinite;
            border-radius: 8px !important;
        }}
        .stProgress > div > div {{
            border-radius: 8px !important;
        }}

        /* ---------- dataframe ---------- */
        [data-testid="stDataFrame"] {{
            border-radius: 12px !important;
            overflow: hidden !important;
            animation: igFadeUp .5s ease both;
        }}

        /* ---------- sidebar ---------- */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, rgba(108,92,231,0.05), rgba(0,180,216,0.02));
            border-right: 1px solid rgba(108,92,231,0.10);
        }}
        section[data-testid="stSidebar"] .stRadio label {{
            border-radius: 10px !important;
            padding: 6px 10px !important;
            margin-bottom: 2px;
            transition: background-color .2s ease, transform .15s ease, color .2s ease !important;
        }}
        section[data-testid="stSidebar"] .stRadio label:hover {{
            background-color: rgba(108,92,231,0.10) !important;
            transform: translateX(3px);
        }}
        section[data-testid="stSidebar"] .stRadio label:has(input:checked) {{
            background: linear-gradient(90deg, var(--ig-primary), var(--ig-primary-2)) !important;
            color: white !important;
            font-weight: 600;
            box-shadow: 0 4px 14px rgba(108,92,231,0.35);
        }}
        section[data-testid="stSidebar"] .stCheckbox label:has(input:checked) {{
            color: var(--ig-primary) !important;
            font-weight: 600;
        }}

        /* ---------- headings ---------- */
        h1, h2, h3 {{
            transition: letter-spacing .3s ease;
        }}

        /* ---------- scrollbar ---------- */
        ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
        ::-webkit-scrollbar-thumb {{
            background: linear-gradient(180deg, var(--ig-primary), var(--ig-primary-2));
            border-radius: 8px;
        }}
        ::-webkit-scrollbar-track {{ background: transparent; }}

        /* ---------- spinner ---------- */
        div[data-testid="stSpinner"] > div {{
            border-top-color: var(--ig-primary) !important;
        }}

        /* ---------- custom components below ---------- */
        .ig-hero {{
            display: flex; align-items: center; gap: 14px;
            padding: 4px 0 2px 0;
            animation: igFadeUp .5s ease both;
        }}
        .ig-hero-icon {{
            font-size: 34px;
            display: inline-block;
            animation: igFloat 3.2s ease-in-out infinite;
        }}
        @keyframes igFloat {{
            0%, 100% {{ transform: translateY(0) rotate(0deg); }}
            50% {{ transform: translateY(-5px) rotate(-3deg); }}
        }}
        .ig-hero-title {{
            font-size: 1.65rem; font-weight: 800; margin: 0;
            background: linear-gradient(120deg, var(--ig-primary), var(--ig-primary-2));
            background-size: 200% auto;
            -webkit-background-clip: text; background-clip: text; color: transparent;
            animation: igGradientShift 5s ease infinite;
        }}
        .ig-hero-subtitle {{
            font-size: 0.92rem; color: rgba(120,120,140,0.9); margin-top: 2px;
        }}

        /* stepper */
        .ig-stepper {{
            display: flex; align-items: center; width: 100%;
            margin: 6px 0 22px 0; animation: igFadeUp .5s ease both;
        }}
        .ig-step {{ display: flex; flex-direction: column; align-items: center; min-width: 46px; }}
        .ig-step-circle {{
            width: 32px; height: 32px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 0.78rem; font-weight: 700;
            border: 2px solid #d8d8e6; color: #9a9ab0; background: white;
            transition: all .35s ease;
        }}
        .ig-step-label {{
            font-size: 0.66rem; margin-top: 5px; text-align: center; color: #9a9ab0;
            max-width: 78px; line-height: 1.1; transition: color .35s ease;
        }}
        .ig-step.done .ig-step-circle {{
            background: linear-gradient(120deg, var(--ig-good), #34d399);
            border-color: transparent; color: white;
        }}
        .ig-step.done .ig-step-label {{ color: var(--ig-good); font-weight: 600; }}
        .ig-step.active .ig-step-circle {{
            background: linear-gradient(120deg, var(--ig-primary), var(--ig-primary-2));
            border-color: transparent; color: white;
            animation: igPulse 1.7s ease-in-out infinite;
        }}
        .ig-step.active .ig-step-label {{ color: var(--ig-primary); font-weight: 700; }}
        @keyframes igPulse {{
            0% {{ box-shadow: 0 0 0 0 rgba(108,92,231,0.45); }}
            70% {{ box-shadow: 0 0 0 9px rgba(108,92,231,0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(108,92,231,0); }}
        }}
        .ig-step-line {{
            flex: 1; height: 3px; margin: 0 2px 18px 2px; border-radius: 3px;
            background: #e4e4ee; transition: background 0.6s ease;
        }}
        .ig-step-line.done {{
            background: linear-gradient(90deg, var(--ig-good), var(--ig-primary));
        }}

        /* score ring */
        .ig-ring-wrap {{
            display: inline-flex; flex-direction: column; align-items: center;
            padding: 6px 10px; animation: igFadeUp .5s ease both;
        }}
        .ig-ring-center {{
            font-weight: 800; font-size: 1.05rem;
        }}
        .ig-ring-title {{
            font-size: 0.78rem; color: rgba(120,120,140,0.9); margin-top: 4px; font-weight: 600;
            text-align: center;
        }}

        /* chips */
        .ig-chip-row {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 4px 0 2px 0; }}
        .ig-chip {{
            display: inline-block; padding: 4px 11px; border-radius: 999px;
            font-size: 0.78rem; font-weight: 600; opacity: 0;
            animation: igChipIn .35s ease forwards;
            transition: transform .15s ease;
        }}
        .ig-chip:hover {{ transform: translateY(-2px) scale(1.04); }}
        @keyframes igChipIn {{
            from {{ opacity: 0; transform: translateY(6px) scale(.9); }}
            to   {{ opacity: 1; transform: translateY(0) scale(1); }}
        }}
        .ig-chip.good {{ background: rgba(16,185,129,0.12); color: #047857; border: 1px solid rgba(16,185,129,0.3); }}
        .ig-chip.bad  {{ background: rgba(239,68,68,0.10); color: #b91c1c; border: 1px solid rgba(239,68,68,0.28); }}
        .ig-chip.neutral {{ background: rgba(108,92,231,0.10); color: #5b3fd6; border: 1px solid rgba(108,92,231,0.28); }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(icon: str, title: str, subtitle: str = ""):
    """Animated hero header used in place of st.header()."""
    sub_html = f'<div class="ig-hero-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div class="ig-hero">
            <span class="ig-hero-icon">{icon}</span>
            <div>
                <p class="ig-hero-title">{title}</p>
                {sub_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def stepper(steps, current_index: int):
    """Animated horizontal progress stepper for the overall workflow."""
    parts = ['<div class="ig-stepper">']
    n = len(steps)
    for i, label in enumerate(steps):
        if i < current_index:
            state, icon = "done", "✓"
        elif i == current_index:
            state, icon = "active", str(i + 1)
        else:
            state, icon = "todo", str(i + 1)
        parts.append(
            f'<div class="ig-step {state}">'
            f'<div class="ig-step-circle">{icon}</div>'
            f'<div class="ig-step-label">{label}</div>'
            f"</div>"
        )
        if i < n - 1:
            line_state = "done" if i < current_index else "todo"
            parts.append(f'<div class="ig-step-line {line_state}"></div>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def score_ring(label: str, value, max_value=100, size=112, help_text=""):
    """Animated circular progress ring (pure SVG + CSS, no JS needed)."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        v = 0.0
    m = float(max_value) or 100.0
    pct = max(0.0, min(1.0, v / m))

    if pct >= 0.75:
        c1, c2 = GOOD, "#34d399"
    elif pct >= 0.45:
        c1, c2 = PRIMARY, PRIMARY_2
    else:
        c1, c2 = WARN, BAD

    radius = 46
    circumference = 2 * 3.14159265 * radius
    offset = circumference * (1 - pct)
    uid = uuid.uuid4().hex[:8]
    display_val = value if isinstance(value, str) else round(v, 1) if v != int(v) else int(v)

    st.markdown(
        f"""
        <div class="ig-ring-wrap">
            <svg width="{size}" height="{size}" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="{radius}" stroke="#e9e9f4" stroke-width="10" fill="none"/>
                <circle cx="60" cy="60" r="{radius}" stroke="url(#grad{uid})" stroke-width="10"
                    fill="none" stroke-linecap="round"
                    stroke-dasharray="{circumference:.2f}"
                    stroke-dashoffset="{circumference:.2f}"
                    transform="rotate(-90 60 60)"
                    style="animation: igRingFill{uid} 1.1s cubic-bezier(.2,.8,.2,1) forwards .15s;"/>
                <defs>
                    <linearGradient id="grad{uid}" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stop-color="{c1}"/>
                        <stop offset="100%" stop-color="{c2}"/>
                    </linearGradient>
                </defs>
                <text x="60" y="65" text-anchor="middle" font-size="22" font-weight="800" fill="#2d2d3a">{display_val}</text>
            </svg>
            <div class="ig-ring-title">{label}{f" · {help_text}" if help_text else ""}</div>
        </div>
        <style>
            @keyframes igRingFill{uid} {{ to {{ stroke-dashoffset: {offset:.2f}; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def chip_row(items, tone="neutral"):
    """Render a staggered fade-in row of pill chips. tone: good|bad|neutral"""
    items = [i for i in (items or []) if i]
    if not items:
        st.caption("—")
        return
    chips = "".join(
        f'<span class="ig-chip {tone}" style="animation-delay:{i*0.05:.2f}s">{txt}</span>'
        for i, txt in enumerate(items)
    )
    st.markdown(f'<div class="ig-chip-row">{chips}</div>', unsafe_allow_html=True)


def divider_glow():
    """A subtle animated gradient divider, nicer than st.divider()."""
    st.markdown(
        """
        <div style="height:2px;border-radius:2px;margin:14px 0;
             background:linear-gradient(90deg, rgba(108,92,231,0), rgba(108,92,231,0.55), rgba(0,180,216,0.55), rgba(0,180,216,0));
             background-size:200% 100%; animation: igGradientShift 4s ease infinite;"></div>
        """,
        unsafe_allow_html=True,
    )
