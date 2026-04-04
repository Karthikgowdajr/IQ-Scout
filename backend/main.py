from fastapi import FastAPI
from pydantic import BaseModel
import json
import os

from iq_scout.agents.prospect_scraper import scrape_prospect
from iq_scout.agents.analysis_agent import run_analysis

app = FastAPI()


# -------------------------
# REQUEST MODEL
# -------------------------
class AnalyzeRequest(BaseModel):
    url: str


# -------------------------
# HEALTH CHECK
# -------------------------
@app.get("/")
def home():
    return {"message": "Backend running 🚀"}


# -------------------------
# MAIN PIPELINE
# -------------------------
@app.post("/analyze")
def analyze(req: AnalyzeRequest):

    try:
        # STEP 1: scrape
        prospect_data = scrape_prospect(req.url)



        # STEP 2: analyze
        result = run_analysis(prospect_data)

        # STEP 3: SAVE FILE (THIS IS NEW)
        output_path = "iq_scout/data/raw/analysis_result.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        # STEP 4: return
        return {
            "status": "success",
            "analysis": result
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }