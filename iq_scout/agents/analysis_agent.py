from langgraph.graph import StateGraph, END
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
from google import genai
from openai import OpenAI
import os
import json
import re
import time
from typing import TypedDict

# -------------------------
# SETUP
# -------------------------
load_dotenv()

# 🔵 Gemini (Primary)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 🔴 OpenRouter (Fallback)
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# 🔒 Safety Limits
CALL_COUNT = 0
MAX_CALLS = 50


# -------------------------
# LLM CALLS
# -------------------------
def openrouter_call(prompt: str) -> str:
    response = openrouter_client.chat.completions.create(
        model="mistralai/mistral-7b-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content


def call_llm(prompt: str, retries=3):
    global CALL_COUNT

    if CALL_COUNT >= MAX_CALLS:
        raise Exception("⚠️ Daily LLM call limit reached")

    CALL_COUNT += 1

    print(f"🔍 Prompt size: {len(prompt)} chars")

    for attempt in range(retries):
        try:
            # 🔵 PRIMARY: GEMINI
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            text = response.text

            if not text or len(text.strip()) < 10:
                raise Exception("Empty response")

            return text

        except Exception as e:
            print(f"⚠️ Gemini error: {e}")

            # 🔴 FALLBACK
            if "429" in str(e) or "quota" in str(e).lower():
                print("🔁 Switching to OpenRouter fallback...")
                try:
                    return openrouter_call(prompt)
                except Exception as fallback_error:
                    print(f"❌ OpenRouter failed: {fallback_error}")

            time.sleep(3)

    raise Exception("LLM failed after retries")


# -------------------------
# JSON SAFE PARSE
# -------------------------
def safe_json_parse(text: str):
    if not text or len(text.strip()) < 5:
        raise Exception("Invalid empty JSON")

    try:
        return json.loads(text)
    except:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise


# -------------------------
# VECTOR DB
# -------------------------
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vectorstore = Chroma(
    persist_directory="iq_scout/data/embeddings",
    embedding_function=embeddings
)


# -------------------------
# STATE
# -------------------------
class ScoutState(TypedDict):
    prospect_data: dict
    company_summary: dict
    pain_points: list
    igniteiq_context: str
    solution_match: dict
    deal_score: str


# -------------------------
# NODE 1: EXTRACT
# -------------------------
def extract_node(state: ScoutState) -> ScoutState:
    print("\n  [Node 1] Extracting company profile...")

    prospect = state["prospect_data"]

    combined_text = f"""
HOMEPAGE:
{prospect.get('homepage', '')[:1200]}

JOBS PAGE:
{prospect.get('jobs', '')[:800]}

RECENT NEWS:
{prospect.get('news', '')[:500]}
"""

    prompt = f"""
You are an AI solutions analyst.

Analyze this company and return structured JSON.

CONTENT:
{combined_text}

Also evaluate if this is a good AI client.

Scoring Rules:
- "high" → Strong AI need + enterprise scale + clear pain
- "medium" → Some opportunity but unclear urgency
- "low" → Weak AI need

IMPORTANT:
- Return EXACTLY 3 pain points (no more, no less)
- Avoid duplicates in pain points
- Be concise and avoid long paragraphs

INSTRUCTIONS:
- Pain points must be specific and grounded in company context (products, hiring, or news)
- Identify key decision-makers or leaders if possible
- Identify recent trigger events (growth, hiring, acquisitions, announcements)
- Identify internal AI systems (if any) and explain competitive risk
- Suggest best outreach channel for this company
- Pain points MUST reference specific products, roles, or signals (e.g., ManageEngine, Zoho Desk, CRM, ITSM jobs)
- Avoid generic AI statements
- Explicitly identify internal AI systems (e.g., Zia) and explain how they affect positioning

    Return ONLY JSON:
{{
    "company_name": "",
    "industry": "",
    "what_they_do": "",
    "current_tech_stack": "",
    "team_size_hint": "",
    "pain_points": ["", "", ""],
    "ai_maturity": "low/medium/high",
    "deal_score": "low/medium/high",
    "deal_reason": "",
    "confidence": "low/medium/high",
    "fit_type": "ideal/okay/poor",
    "deal_priority": "P1/P2/P3",

    "key_contacts": ["", ""],
    "trigger_events": ["", ""],
    "competitive_risk": "",
    "suggested_outreach_channel": ""
}}
"""

    try:
        raw = call_llm(prompt)
        parsed = safe_json_parse(raw)
    except Exception as e:
        print(f"❌ Extract failed: {e}")
        parsed = {}

    # -------------------------
    # 🔥 CLEAN PAIN POINTS
    # -------------------------
    raw_pain_points = parsed.get("pain_points", [])

    clean_pain_points = []
    seen = set()

    for p in raw_pain_points:
        if not isinstance(p, str):
            continue

        p_clean = p.strip()

        if len(p_clean) < 10:
            continue

        if p_clean.lower() in seen:
            continue

        seen.add(p_clean.lower())
        clean_pain_points.append(p_clean)

    # enforce exactly 3
    state["pain_points"] = clean_pain_points[:3]

    # -------------------------
    # OTHER FIELDS
    # -------------------------
    state["company_summary"] = parsed
    state["deal_score"] = parsed.get("deal_score", "unknown")
    state["deal_reason"] = parsed.get("deal_reason", "")
    state["deal_priority"] = parsed.get("deal_priority", "unknown")
    state["confidence"] = parsed.get("confidence", "unknown")
    state["fit_type"] = parsed.get("fit_type", "unknown")
    state["key_contacts"] = parsed.get("key_contacts", [])
    state["trigger_events"] = parsed.get("trigger_events", [])
    state["competitive_risk"] = parsed.get("competitive_risk", "")
    state["suggested_outreach_channel"] = parsed.get("suggested_outreach_channel", "")

    print(f"  Company: {parsed.get('company_name')}")
    print(f"  AI maturity: {parsed.get('ai_maturity')}")
    print(f"  Pain points: {state['pain_points']}")

    return state

# -------------------------
# NODE 2: RAG
# -------------------------
def rag_match_node(state: ScoutState) -> ScoutState:
    print("\n  [Node 2] RAG retrieval...")

    pain_points = state["pain_points"]
    query = " ".join(pain_points) if pain_points else "enterprise AI automation"

    try:
        docs = vectorstore.similarity_search(query, k=5)
    except Exception as e:
        print(f"❌ RAG failed: {e}")
        docs = []

    if not docs:
        context = "Enterprise AI automation, RAG systems, workflow automation"
    else:
        clean_chunks = []
        seen = set()

        for doc in docs[:3]:
            text = doc.page_content.strip()

            if len(text) < 100:
                continue

            if text in seen:
                continue

            seen.add(text)
            clean_chunks.append(text[:500])

        context = "\n\n".join(clean_chunks)

    state["igniteiq_context"] = context
    print(f"  Retrieved {len(docs)} docs")

    return state

# -------------------------
# NODE 3: SOLUTION
# -------------------------
def solution_match_node(state: ScoutState) -> ScoutState:
    print("\n  [Node 3] Generating solution...")

    if not state["company_summary"]:
        print("⚠️ Skipping solution")
        return state

    prompt = f"""
You are a senior AI architect and AI sales strategist.

PROSPECT:
{json.dumps(state['company_summary'], indent=2)}

CONTEXT:
{state['igniteiq_context'][:1800]}

IMPORTANT:
- Be technically specific (mention real systems like RAG, fine-tuning, pipelines)
- Avoid vague consulting language
- ROI must be realistic and qualified (no made-up percentages)
- Consider competitive risk (internal AI systems)
- ROI should be grounded in mechanism (how value is created), not vague outcomes

INSTRUCTIONS:
- Suggest a specific first use-case (pilot project) to start engagement


Return ONLY JSON:
{{
    "one_line_pitch": "",
    "short_summary": "",
    "recommended_service": "",
    "why_now": "",
    "priority_action": "",
    "rationale": "",
    "entry_wedge": "",
    "architecture_sketch": [
        "",
        "",
        ""
    ],
    "estimated_roi": "",
    "differentiator": ""
}}
"""

    try:
        raw = call_llm(prompt)
        parsed = safe_json_parse(raw)
    except Exception as e:
        print(f"❌ Solution failed: {e}")
        parsed = {}

    state["solution_match"] = parsed
    return state


# -------------------------
# NODE 4: SCORING
def scoring_node(state: ScoutState) -> ScoutState:
    print("\n  [Node 4] Scoring deal (fallback)...")

    # ✅ Skip if already scored in extract
    if state.get("deal_score") and state["deal_score"] != "unknown":
        print("  ✅ Score already available, skipping scoring node")
        return state

    # fallback condition
    if not state["solution_match"]:
        state["deal_score"] = "unknown"
        state["deal_reason"] = ""
        return state

    prompt = f"""
You are a strict AI sales evaluator.

Evaluate whether this company is a GOOD CLIENT for AI services.

Be critical and realistic — do NOT overrate.

Scoring Rules:
- "high" → Strong AI need + clear pain points + enterprise scale + budget likely
- "medium" → Some AI opportunity but unclear urgency or smaller scale
- "low" → Weak AI need or no clear business value

PROFILE:
{json.dumps(state['company_summary'], indent=2)}

SOLUTION:
{json.dumps(state['solution_match'], indent=2)}

Return ONLY JSON:
{{
    "deal_score": "low/medium/high",
    "reason": ""
}}
"""

    try:
        raw = call_llm(prompt)
        parsed = safe_json_parse(raw)

        state["deal_score"] = parsed.get("deal_score", "unknown")
        state["deal_reason"] = parsed.get("reason", "")

    except Exception as e:
        print(f"❌ Scoring fallback failed: {e}")
        state["deal_score"] = "unknown"
        state["deal_reason"] = ""

    print(f"  Deal score: {state['deal_score']}")
    return state

# -------------------------
# GRAPH
# -------------------------
def build_graph():
    graph = StateGraph(ScoutState)

    graph.add_node("extract", extract_node)
    graph.add_node("rag", rag_match_node)
    graph.add_node("solution", solution_match_node)
    graph.add_node("score", scoring_node)

    graph.set_entry_point("extract")

    graph.add_edge("extract", "rag")
    graph.add_edge("rag", "solution")
    graph.add_edge("solution", "score")
    graph.add_edge("score", END)

    return graph.compile()


# -------------------------
# RUN
# -------------------------
def run_analysis(prospect_data: dict):
    graph = build_graph()

    initial_state = {
        "prospect_data": prospect_data,
        "company_summary": {},
        "pain_points": [],
        "igniteiq_context": "",
        "solution_match": {},
        "deal_score": ""
    }

    return graph.invoke(initial_state)


# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    print("🚀 Running analysis...")

    with open("iq_scout/data/raw/prospect_test.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    result = run_analysis(data)

    print("\n--- RESULT ---")
    print(json.dumps(result, indent=2))

    with open("iq_scout/data/raw/analysis_result.json", "w") as f:
        json.dump(result, f, indent=2)

    print("✅ Done")