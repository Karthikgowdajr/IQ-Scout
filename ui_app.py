import streamlit as st
import streamlit.components.v1 as components
import html as html_module
import json
import os
import requests

# ─────────────────────────────────────────────
# PAGE CONFIG — must be first
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="IQ-Scout · IgniteIQ",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False  # Default: Light (IgniteIQ brand)

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
def inject_css(dark: bool):

    if dark:
        css = """
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        :root {
            --bg:          #0c0d10;
            --bg2:         #13151b;
            --surface:     #1a1d26;
            --surface2:    #20232f;
            --border:      #2a2d3e;
            --border2:     #353848;
            --fire1:       #e84c1e;
            --fire2:       #f5a623;
            --fire-grad:   linear-gradient(135deg, #e84c1e, #f5a623);
            --fire-glow:   rgba(232, 76, 30, 0.2);
            --text:        #f0f2f8;
            --text2:       #9ba3c0;
            --text3:       #565d7a;
            --high:        #22c97a;
            --medium:      #f5a623;
            --low:         #ff4d6d;
            --radius:      12px;
        }
        html, body, .stApp {
    font-family: 'Inter', sans-serif !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* 🔥 Critical Streamlit container fix */
section.main > div {
    background-color: var(--bg) !important;
}

/* Extra safety override */
[data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
}

/* Layout fixes */
.main .block-container { 
    padding: 0 !important; 
    max-width: 100% !important; 
}

.main > div { 
    padding: 0 !important; 
}

/* Hide Streamlit UI */
#MainMenu, footer, header, .stDeployButton { 
    display: none !important; 
}

[data-testid="stToolbar"] { 
    display: none !important; 
}

/* Theme row (navbar last column): pod bg + outlined toggle — dark UI */
div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="stColumn"]:last-child > div,
div[data-testid="stHorizontalBlock"]:first-of-type [data-testid="stColumn"]:last-child [data-testid="stVerticalBlock"] {
    border: 2px solid #e84c1e !important;
    border-radius: 14px !important;
    padding: 12px 16px !important;
    background: #1a1d26 !important;
    box-shadow: 0 2px 16px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255,255,255,0.06) !important;
}
/* st.toggle uses Base Web checkbox — no .stToggle class in newer Streamlit */
[data-baseweb="checkbox"] [data-baseweb="switch"] {
    transform: scale(1.55) !important;
    transform-origin: center right !important;
    border: 2px solid rgba(245, 166, 35, 0.55) !important;
    border-radius: 999px !important;
    background: linear-gradient(135deg, #e84c1e, #f5a623) !important;
    box-shadow: 0 0 0 1px rgba(232, 76, 30, 0.45) !important;
}
[data-baseweb="checkbox"] [data-baseweb="switch"] [data-baseweb="thumb"] {
    border: 2px solid rgba(255, 255, 255, 0.9) !important;
    background: #ffffff !important;
}
[data-baseweb="checkbox"] label,
[data-baseweb="checkbox"] label p,
[data-baseweb="checkbox"] label span,
[data-baseweb="checkbox"] [data-testid="stMarkdownContainer"] p,
[data-baseweb="checkbox"] [data-testid="stMarkdown"] p,
[data-baseweb="checkbox"] [data-testid="stMarkdown"] span {
    font-size: 19px !important;
    font-weight: 700 !important;
    color: #f5a623 !important;
    -webkit-text-fill-color: #f5a623 !important;
}
        """
    else:
        css = """
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        :root {
            --bg:          #ffffff;
            --bg2:         #f7f8fa;
            --surface:     #f2f3f7;
            --surface2:    #ecedf3;
            --border:      #e0e2ec;
            --border2:     #d0d3e0;
            --fire1:       #e84c1e;
            --fire2:       #f5a623;
            --fire-grad:   linear-gradient(135deg, #e84c1e, #f5a623);
            --fire-glow:   rgba(232,76,30,0.15);
            --text:        #0f172a;
            --text2:       #334155;
            --text3:       #64748b;
            --high:        #0d9e62;
            --medium:      #d4890a;
            --low:         #d63050;
            --radius:      12px;
        }
        html, body, .stApp {
    font-family: 'Inter', sans-serif !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* 🔥 CRITICAL: actual Streamlit container */
section.main > div {
    background-color: var(--bg) !important;
}

/* Optional but recommended */
[data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
}

/* Keep your layout fixes */
.main .block-container { 
    padding: 0 !important; 
    max-width: 100% !important; 
}

.main > div { 
    padding: 0 !important; 
}

/* Hide default UI */
#MainMenu, footer, header, .stDeployButton { 
    display: none !important; 
}

[data-testid="stToolbar"] { 
    display: none !important; 
}

/* Theme row (navbar last column): pod — match Streamlit column / vertical block wrappers */
div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="stColumn"]:last-child > div,
div[data-testid="stHorizontalBlock"]:first-of-type [data-testid="stColumn"]:last-child [data-testid="stVerticalBlock"] {
    border: 2px solid #e84c1e !important;
    border-radius: 14px !important;
    padding: 12px 16px !important;
    background: #eef1f7 !important;
    box-shadow: 0 2px 12px rgba(15, 23, 42, 0.08), inset 0 1px 0 rgba(255,255,255,0.9) !important;
}
[data-baseweb="checkbox"] [data-baseweb="switch"] {
    transform: scale(1.55) !important;
    transform-origin: center right !important;
    border: 2px solid #c2410c !important;
    border-radius: 999px !important;
    background: linear-gradient(135deg, #e84c1e, #f5a623) !important;
    box-shadow: 0 0 0 1px rgba(232, 76, 30, 0.5) !important;
}
[data-baseweb="checkbox"] [data-baseweb="switch"] [data-baseweb="thumb"] {
    border: 2px solid #c2410c !important;
    background: #ffffff !important;
}
[data-baseweb="checkbox"] label,
[data-baseweb="checkbox"] label p,
[data-baseweb="checkbox"] label span,
[data-baseweb="checkbox"] [data-testid="stMarkdownContainer"] p,
[data-baseweb="checkbox"] [data-testid="stMarkdownContainer"] span,
[data-baseweb="checkbox"] [data-testid="stMarkdown"] p,
[data-baseweb="checkbox"] [data-testid="stMarkdown"] span {
    font-size: 19px !important;
    font-weight: 700 !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}
        """

    # Shared styles (same in both modes, use CSS vars)
    shared = """
    /* ── Brand (top bar) ── */
    .iq-brand { display: flex; align-items: center; gap: 18px; padding: 10px 0 8px; }
    .iq-flame  { font-size: 52px; line-height: 1; }
    .iq-brand-text { display: flex; flex-direction: column; line-height: 1.05; }
    .iq-brand-name {
        font-size: 38px; font-weight: 800;
        background: var(--fire-grad);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; letter-spacing: -0.45px;
    }
    .iq-brand-tagline {
        font-size: 15px; color: var(--text3);
        letter-spacing: 2.1px; text-transform: uppercase; margin-top: 6px;
    }
    .iq-nav-badge {
        font-size: 18px; padding: 9px 20px; border-radius: 24px;
        background: rgba(232,76,30,0.1); color: var(--fire1);
        border: 1px solid rgba(232,76,30,0.25); font-weight: 600; margin-left: 14px;
    }

    /* ── Hero ── */
    .iq-hero {
        padding: 22px 48px 18px;
        min-height: 0;
        border-bottom: 1px solid var(--border);
    }
    .iq-hero-title {
        font-size: 38px; font-weight: 800;
        letter-spacing: -0.65px; margin-bottom: 8px; color: var(--text);
        line-height: 1.12;
    }
    .iq-hero-title span {
        background: var(--fire-grad);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .iq-hero-sub { font-size: 17px; color: var(--text2); margin-bottom: 0; line-height: 1.5; }

    /* ── Metrics ── */
    .iq-metrics {
        display: grid; grid-template-columns: repeat(4, 1fr);
        gap: 14px; padding: 28px 48px; border-bottom: 1px solid var(--border);
    }
    .iq-metric {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius); padding: 18px 20px;
        position: relative; overflow: hidden;
    }
    .iq-metric::after {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
        background: var(--fire-grad);
    }
    .iq-metric-label {
        font-size: 12px; text-transform: uppercase; letter-spacing: 1.2px;
        color: var(--text3); margin-bottom: 8px; font-weight: 600;
    }
    .iq-metric-value { font-size: 22px; font-weight: 700; text-transform: capitalize; }
    .iq-metric-value.high   { color: var(--high); }
    .iq-metric-value.medium { color: var(--medium); }
    .iq-metric-value.low    { color: var(--low); }
    .iq-metric-value.fire   {
        background: var(--fire-grad);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .iq-metric-value.default { color: var(--text); }

    /* ── Content ── */
    .iq-content { padding: 32px 48px; }

    /* ── Section headers ── */
    .iq-section {
        font-size: 13px; font-weight: 700; text-transform: uppercase;
        letter-spacing: 1.8px; color: var(--text3); margin: 24px 0 12px;
        display: flex; align-items: center; gap: 10px;
    }
    .iq-section::after { content: ''; flex: 1; height: 1px; background: var(--border); }

    /* ── Cards ── */
    .iq-card {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius); padding: 16px 20px; margin-bottom: 10px;
        font-size: 16px; line-height: 1.75; color: var(--text2);
    }
    .iq-card.pain  { border-left: 3px solid var(--fire1); padding-left: 16px; }
    .iq-card.trigger {
        border-left: 3px solid var(--fire2);
        background: rgba(245,166,35,0.05);
    }
    .iq-card.risk {
        border-left: 3px solid var(--low);
        background: rgba(255,77,109,0.05); color: var(--text);
    }
    .iq-card.pitch {
        background: linear-gradient(135deg, rgba(232,76,30,0.07), rgba(245,166,35,0.05));
        border-color: rgba(232,76,30,0.2);
        font-size: 17px; line-height: 1.8; font-style: italic; color: var(--text);
    }
    .iq-card.arch { display: flex; gap: 14px; align-items: flex-start; }
    .iq-arch-num {
        background: var(--fire-grad); color: white;
        min-width: 28px; height: 28px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 13px; font-weight: 800; flex-shrink: 0; margin-top: 2px;
    }

    /* ── Outreach ── */
    .iq-outreach {
        background: var(--surface2); border: 1px solid var(--border);
        border-radius: var(--radius); padding: 22px 24px;
        font-size: 16px; line-height: 1.9;
        white-space: pre-wrap; word-break: break-word; color: var(--text);
        margin-bottom: 8px;
    }

    /* ── Chips ── */
    .iq-chip {
        display: inline-flex; align-items: center; gap: 8px;
        background: var(--surface2); border: 1px solid var(--border);
        border-radius: 40px; padding: 6px 16px 6px 8px;
        font-size: 14px; margin: 4px; color: var(--text2);
    }
    .iq-chip-avatar {
        width: 26px; height: 26px; border-radius: 50%;
        background: var(--fire-grad);
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 12px; font-weight: 700; color: white;
    }

    /* ── Channel tag ── */
    .iq-channel {
        display: inline-block;
        background: rgba(245,166,35,0.1); border: 1px solid rgba(245,166,35,0.25);
        color: var(--fire2); font-size: 14px;
        padding: 6px 16px; border-radius: 20px; margin-top: 6px;
    }

    /* ── Company ── */
    .iq-company-name {
        font-size: 30px; font-weight: 800;
        letter-spacing: -0.4px; margin-bottom: 6px; color: var(--text);
    }
    .iq-company-industry { font-size: 16px; color: var(--text2); }

    /* ── CTA Banner (IgniteIQ orange footer style) ── */
    .iq-cta-banner {
        background: var(--fire-grad); border-radius: var(--radius);
        padding: 30px 36px; text-align: center; color: #ffffff !important; margin-top: 32px;
        border: 1px solid rgba(255,255,255,0.35);
        box-shadow: 0 4px 24px rgba(232, 76, 30, 0.25);
    }
    .iq-cta-banner h3 {
        font-size: 23px; font-weight: 800; margin-bottom: 8px;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    .iq-cta-banner p {
        font-size: 16px; font-weight: 500; line-height: 1.55;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        opacity: 1 !important;
    }

    /* ── Footer ── */
    .iq-footer {
        display: flex; justify-content: space-between; align-items: center;
        padding: 18px 48px; font-size: 14px; color: var(--text3);
        border-top: 1px solid var(--border); margin-top: 8px;
    }
    .iq-footer-brand {
        display: flex; align-items: center; gap: 6px;
    }
    .iq-footer-brand span.name {
        background: var(--fire-grad);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; font-weight: 700;
    }

    /* ── Streamlit overrides ── */
    .stTextInput > div > div {
        background: var(--surface) !important;
        border: 1.5px solid var(--border2) !important;
        border-radius: 10px !important;
    }
    .stTextInput input {
        color: var(--text) !important; font-size: 16px !important;
        padding: 12px 18px !important; background: transparent !important;
        font-family: 'Inter', sans-serif !important;
        caret-color: var(--fire1) !important;
    }
    .stTextInput input::placeholder {
        color: var(--text3) !important;
        opacity: 1 !important;
    }
    div[data-baseweb="input"] input::placeholder {
        color: var(--text3) !important;
        opacity: 1 !important;
    }
    .stButton > button {
        background: var(--fire-grad) !important;
        color: white !important; border: none !important;
        border-radius: 10px !important; font-weight: 700 !important;
        font-size: 16px !important; font-family: 'Inter', sans-serif !important;
        box-shadow: 0 4px 16px var(--fire-glow) !important;
    }
    .stButton > button:hover { opacity: 0.92 !important; }
    .stTabs [data-baseweb="tab-list"] {
        background: var(--surface) !important; border-radius: 10px !important;
        padding: 4px !important; gap: 4px !important;
        border: 1px solid var(--border) !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 7px !important; font-size: 15px !important;
        font-weight: 600 !important; color: var(--text2) !important;
        padding: 10px 24px !important; font-family: 'Inter', sans-serif !important;
    }
    .stTabs [aria-selected="true"] {
        background: var(--fire-grad) !important; color: white !important;
    }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 1.2rem !important; }
    hr { border-color: var(--border) !important; margin: 0 !important; }
    div[data-testid="stHorizontalBlock"] { gap: 20px !important; }
    [data-testid="stColumn"] { color: var(--text) !important; }
    [data-testid="stMarkdown"] { color: var(--text) !important; }
    [data-testid="stMarkdown"] p, [data-testid="stMarkdown"] li { color: var(--text2) !important; }
    /* CTA on orange gradient: global markdown <p> rules must not mute this copy */
    [data-testid="stMarkdown"] .iq-cta-banner,
    [data-testid="stMarkdown"] .iq-cta-banner h3,
    [data-testid="stMarkdown"] .iq-cta-banner p {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        opacity: 1 !important;
    }

    [data-testid="stCaption"] { color: var(--text3) !important; }
    .stException, .stAlert { color: inherit !important; }
    """

    # `shared` runs after mode `css`. Newer Streamlit toggles omit `.stToggle`; target Base Web checkbox + high specificity.
    theme_toggle_fix = """
        div[data-testid="stHorizontalBlock"]:first-of-type [data-testid="stColumn"]:last-child [data-testid="stVerticalBlock"],
        div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="stColumn"]:last-child > div {
            background: POD_BG !important;
        }
        html body .stApp section.main [data-baseweb="checkbox"] label,
        html body .stApp section.main [data-baseweb="checkbox"] label p,
        html body .stApp section.main [data-baseweb="checkbox"] label span,
        html body .stApp section.main [data-baseweb="checkbox"] [data-testid="stMarkdownContainer"],
        html body .stApp section.main [data-baseweb="checkbox"] [data-testid="stMarkdownContainer"] p,
        html body .stApp section.main [data-baseweb="checkbox"] [data-testid="stMarkdownContainer"] span,
        html body .stApp section.main [data-baseweb="checkbox"] [data-testid="stMarkdown"] p,
        html body .stApp section.main [data-baseweb="checkbox"] [data-testid="stMarkdown"] span {
            color: ORANGE_TEXT !important;
            -webkit-text-fill-color: ORANGE_TEXT !important;
        }
        html body .stApp section.main [data-baseweb="checkbox"] [data-baseweb="switch"] {
            border: 2px solid ORANGE_BORDER !important;
            box-shadow: 0 0 0 1px rgba(232, 76, 30, 0.45) !important;
            background: linear-gradient(135deg, #e84c1e, #f5a623) !important;
        }
        html body .stApp section.main [data-baseweb="checkbox"] [data-baseweb="switch"] [data-baseweb="thumb"] {
            border: 2px solid ORANGE_BORDER !important;
            background: #ffffff !important;
        }
        """

    if dark:
        theme_toggle_fix = (
            theme_toggle_fix.replace("ORANGE_TEXT", "#f5a623")
            .replace("ORANGE_BORDER", "rgba(245, 166, 35, 0.65)")
            .replace("POD_BG", "#000000")
        )
    else:
        theme_toggle_fix = (
            theme_toggle_fix.replace("ORANGE_TEXT", "#000000")
            .replace("ORANGE_BORDER", "#c2410c")
            .replace("POD_BG", "#eef1f7")
        )

    st.markdown(f"<style>{css}{shared}{theme_toggle_fix}</style>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def score_class(val):
    v = str(val).lower()
    if v in ("high", "ideal", "strong", "excellent"): return "high"
    if v in ("medium", "moderate", "good", "okay"):           return "medium"
    if v in ("low", "weak", "poor"):                  return "low"
    return "default"

def iq_card(content, kind=""):
    st.markdown(f"<div class='iq-card {kind}'>{content}</div>", unsafe_allow_html=True)

def iq_section(icon, title):
    st.markdown(f"<div class='iq-section'>{icon} {title}</div>", unsafe_allow_html=True)

def arch_step(num, text):
    safe = html_module.escape(str(text))
    st.markdown(f"""
    <div class='iq-card arch'>
        <div class='iq-arch-num'>{num}</div>
        <div style='color:var(--text2); font-size:16px; line-height:1.7'>{safe}</div>
    </div>""", unsafe_allow_html=True)

def chip(name):
    initial = name[0].upper() if name else "?"
    return f"<span class='iq-chip'><span class='iq-chip-avatar'>{initial}</span>{name}</span>"

def metric_html(label, value, cls="default"):
    lab = html_module.escape(str(label))
    val = html_module.escape(str(value if value not in (None, "") else "—"))
    cl = html_module.escape(cls)
    return (
        f'<div class="iq-metric">'
        f'<div class="iq-metric-label">{lab}</div>'
        f'<div class="iq-metric-value {cl}">{val}</div>'
        f"</div>"
    )


def copy_to_clipboard_button(text: str, label: str, height: int = 52):
    """Single copy control for outreach text (runs in components iframe)."""
    payload = json.dumps(text)
    components.html(
        f"""
        <div style="margin:4px 0 12px 0;font-family:system-ui,-apple-system,sans-serif;">
          <button type="button"
            onclick="navigator.clipboard.writeText({payload}).catch(function(){{}})"
            style="background:linear-gradient(135deg,#e84c1e,#f5a623);color:#fff;border:none;
            border-radius:10px;padding:8px 20px;font-weight:700;cursor:pointer;font-size:14px;">
            {html_module.escape(label)}
          </button>
        </div>
        """,
        height=height,
    )

def load_result():
    path = "iq_scout/data/raw/analysis_result.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


# ─────────────────────────────────────────────
# INJECT CSS
# ─────────────────────────────────────────────
inject_css(st.session_state.dark_mode)


# ─────────────────────────────────────────────
# NAVBAR
# ─────────────────────────────────────────────
nav_left, nav_right = st.columns([6, 1])
with nav_left:
    st.markdown("""
    <div class="iq-brand">
        <span class="iq-flame">🔥</span>
        <div class="iq-brand-text">
            <span class="iq-brand-name">IgniteIQ</span>
            <span class="iq-brand-tagline">Spark Innovation</span>
        </div>
        <span class="iq-nav-badge">IQ-Scout · Sales Intelligence</span>
    </div>
    """, unsafe_allow_html=True)

with nav_right:
    # Single control: label shows the mode you switch *to* (Light vs Dark)
    mode_label = "☀️ Light" if st.session_state.dark_mode else "🌙 Dark"
    toggled = st.toggle(mode_label, value=st.session_state.dark_mode, key="theme_toggle")
    if toggled != st.session_state.dark_mode:
        st.session_state.dark_mode = toggled
        st.rerun()

st.markdown("<hr>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HERO — URL INPUT
# ─────────────────────────────────────────────
st.markdown("""
<div class="iq-hero">
    <div class="iq-hero-title">Scout your next <span>high-value deal</span></div>
    <div class="iq-hero-sub">
        IQ-Scout scrapes, analyzes, and generates a full sales intelligence brief instantly.
    </div>
</div>
""", unsafe_allow_html=True)

col_in, col_btn = st.columns([5, 1])
with col_in:
    url = st.text_input(
        "Company URL",
        placeholder="https://www.company.com --->  paste URL here",
        label_visibility="collapsed",
    )
with col_btn:
    run = st.button("🚀  Analyze", use_container_width=True)



if run and url:

    # 🚫 Block self-analysis (IgniteIQ)
    blocked_domains = ["igniteiq.ai", "www.igniteiq.ai", "https://igniteiq.ai/", "https://igniteiq.ai/portfolio", "https://igniteiq.ai/contact", "https://igniteiq.ai/services", "https://igniteiq.ai"]

    if any(domain in url.lower() for domain in blocked_domains):
        st.markdown("""
        <div class='iq-card risk'>
        ⚠️ You're trying to analyze IgniteIQ (the solution provider).<br><br>

        🎯 IQ-Scout works best when analyzing:<br>
        • Potential clients<br>
        • Target companies<br>
        • Leads you want to sell to<br><br>

        👉 Please enter a different company URL.
        </div>
        """, unsafe_allow_html=True)
        st.stop()

       # ✅ Show spinner (ONLY short message)
    with st.spinner("🔄 Running analysis..."):

        st.markdown("""
<div style="margin-top:10px; font-size:14px; color:var(--text2);">
⏳ Scraping and analysis time varies based on 🔍 website size.<br>
Since we're on a <b>Free tier</b>, this may take a minute — but the 🧠 insights are ⚡worth the wait.
</div>
""", unsafe_allow_html=True)

        try:
            response = requests.post(
                "https://iq-scout.up.railway.app/analyze",
                json={"url": url}
            )

            if response.status_code == 200:
                data = response.json()

                if data.get("status") == "success":
                    st.toast("✅ Analysis complete!")

                    # Save result locally so your UI can load it
                    output_path = "iq_scout/data/raw/analysis_result.json"
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)

                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(data["analysis"], f, indent=2)

                    st.rerun()

                else:
                    st.error(data.get("message", "Unknown error"))

            else:
                st.error("Backend error")

        except Exception as e:
            st.error(f"Connection error: {e}")


# ─────────────────────────────────────────────
# LOAD & GATE
# ─────────────────────────────────────────────
result = load_result()

if not result:
    dark = st.session_state.dark_mode
    st.markdown(f"""
    <div style="text-align:center; padding:80px 20px; color:var(--text3);">
        <div style="font-size:52px; margin-bottom:20px;">🔥</div>
        <div style="font-size:20px; font-weight:800; margin-bottom:8px; color:var(--text);">
            Ready to ignite your pipeline
        </div>
        <div style="font-size:14px;">Enter a company URL above and click Analyze</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ─────────────────────────────────────────────
# PARSE DATA
# ─────────────────────────────────────────────
summary  = result.get("company_summary", {})
solution = result.get("solution_match",  {})
outreach = result.get("outreach",        {})
pain_pts = result.get("pain_points",     [])

deal_score  = str(result.get("deal_score",          "—"))
ai_maturity = str(summary.get("ai_maturity",        "—"))
fit_type    = str(summary.get("fit_type",           "—"))
confidence  = str(summary.get("confidence", summary.get("deal_priority", "—")))


# ─────────────────────────────────────────────
# METRIC STRIP
# ─────────────────────────────────────────────
st.html(
    "<div class='iq-metrics'>"
    + metric_html("Deal Score", deal_score, score_class(deal_score))
    + metric_html("AI Maturity", ai_maturity, score_class(ai_maturity))
    + metric_html("Fit Type", fit_type, score_class(fit_type))
    + metric_html("Confidence", confidence, score_class(confidence))
    + "</div>"
)


# ─────────────────────────────────────────────
# COMPANY HEADER
# ─────────────────────────────────────────────
st.markdown("<div class='iq-content'>", unsafe_allow_html=True)
st.markdown(f"""
<div style="margin-bottom:20px;">
    <div class="iq-company-name">{summary.get('company_name','—')}</div>
    <div class="iq-company-industry">{summary.get('industry','—')}</div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊  Insights", "📄  Report", "✉️  Outreach"])


# ════════════════════════════════════
# TAB 1 — INSIGHTS
# ════════════════════════════════════
with tab1:
    col_a, col_b = st.columns(2, gap="large")

    with col_a:
        iq_section("🏢", "Company Overview")
        iq_card(summary.get("what_they_do", "—"))

        iq_section("⚡", "Pain Points")
        for p in (pain_pts or ["No pain points identified."]):
            iq_card(
                f"<span style='color:var(--fire1);margin-right:8px;'>◆</span> {p}",
                "pain"
            )

        iq_section("⚔️", "Competitive Risk")
        iq_card(summary.get("competitive_risk", "—"), "risk")

    with col_b:
        iq_section("🎯", "Trigger Events")
        triggers = summary.get("trigger_events", [])
        if triggers:
            for t in triggers:
                iq_card(f"<span style='color:var(--fire2);margin-right:8px;'>▶</span> {t}", "trigger")
        else:
            iq_card("No trigger events detected.")

        iq_section("👤", "Key Contacts")
        contacts = summary.get("key_contacts", [])
        if contacts:
            st.markdown(
                f"<div style='margin-bottom:12px;'>{''.join(chip(c) for c in contacts)}</div>",
                unsafe_allow_html=True
            )
        else:
            iq_card("No contacts identified.")

        iq_section("📡", "Suggested Outreach Channel")
        channel = summary.get("suggested_outreach_channel", "")
        st.markdown(
            f"<div class='iq-channel'>📡 {channel}</div>" if channel else "<div class='iq-card'>—</div>",
            unsafe_allow_html=True
        )

        iq_section("🛠️", "Tech Stack Signals")
        iq_card(summary.get("current_tech_stack", "—"))


# ════════════════════════════════════
# TAB 2 — REPORT
# ════════════════════════════════════
with tab2:
    pitch = solution.get("one_line_pitch", solution.get("short_summary", ""))
    if pitch:
        iq_section("💡", "One-Line Pitch")
        iq_card(pitch, "pitch")

    col_r1, col_r2 = st.columns(2, gap="large")

    with col_r1:
        iq_section("🚀", "Recommended Solution")
        iq_card(solution.get("recommended_service", "—"))

        iq_section("⏰", "Why Now")
        iq_card(solution.get("why_now", "—"))

        iq_section("📊", "Estimated ROI")
        iq_card(solution.get("estimated_roi", "—"))

        iq_section("🏆", "Differentiator")
        iq_card(solution.get("differentiator", "—"))

    with col_r2:
        iq_section("🏗️", "Architecture Sketch")
        arch = solution.get("architecture_sketch", [])
        if arch:
            for i, step in enumerate(arch, 1):
                arch_step(i, step)
        else:
            iq_card("No architecture sketch generated.")

        iq_section("🎯", "Priority Action")
        iq_card(solution.get("priority_action", "—"))

        iq_section("📝", "Rationale")
        iq_card(solution.get("rationale", "—"))

    # IgniteIQ-style orange CTA banner
    st.markdown("""
    <div class="iq-cta-banner">
        <h3>Ready to turn this intel into a deal?</h3>
        <p>Head to the Outreach tab — your personalized cold email and LinkedIn message are ready to send.</p>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════
# TAB 3 — OUTREACH
# ════════════════════════════════════
with tab3:
    col_o1, col_o2 = st.columns(2, gap="large")

    with col_o1:
        iq_section("📧", "Cold Email")
        email_text = outreach.get("cold_email", "")
        if email_text:
            safe_email = html_module.escape(email_text)
            st.markdown(f"<div class='iq-outreach'>{safe_email}</div>", unsafe_allow_html=True)
            
        else:
            iq_card("No email draft generated.")

    with col_o2:
        iq_section("💼", "LinkedIn DM")
        linkedin_text = outreach.get("linkedin_dm", "")
        if linkedin_text:
            safe_li = html_module.escape(linkedin_text)
            st.markdown(f"<div class='iq-outreach'>{safe_li}</div>", unsafe_allow_html=True)
            
        else:
            iq_card("No LinkedIn DM generated.")

    pitch_opener = outreach.get("pitch_opener", "")
    if pitch_opener:
        iq_section("🔥", "Pitch Opener")
        safe_po = html_module.escape(pitch_opener)
        st.markdown(f"""
        <div class='iq-card pitch' style='text-align:center; font-size:18px; padding:22px 28px;'>
            "{safe_po}"
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # close iq-content


# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("""
<div class="iq-footer">
    <div class="iq-footer-brand">
        <span>🔥</span>
        <span class="name">IgniteIQ</span>
        <span>· Spark Innovation</span>
    </div>
    <div>© 2026 IIQ. All rights reserved.</div>
    <div>Privacy Policy · Contact Us</div>
</div>
""", unsafe_allow_html=True)