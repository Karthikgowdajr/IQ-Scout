from firecrawl import FirecrawlApp
from dotenv import load_dotenv
import os
import json

# -------------------------
# SETUP
# -------------------------
load_dotenv()

app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

print("🔥 FILE STARTED")


# -------------------------
# HELPERS
# -------------------------
def extract_markdown_safe(res):
    if hasattr(res, "markdown"):
        return res.markdown or ""
    elif isinstance(res, dict):
        return res.get("markdown", "") or ""
    return ""


def extract_company_name(url: str):
    domain = url.replace("https://", "").replace("http://", "").replace("www.", "")
    return domain.split(".")[0]


# -------------------------
# MAIN FUNCTION
# -------------------------
def scrape_prospect(url: str) -> dict:
    print(f"\n🚀 Scraping prospect: {url}")

    result = {
        "url": url,
        "homepage": "",
        "jobs": "",
        "news": ""
    }

    # -------------------------
    # 1. HOMEPAGE
    # -------------------------
    try:
        print("  🔹 Scraping homepage...")
        res = app.scrape(url, formats=["markdown", "html"])
        content = extract_markdown_safe(res)

        if content and len(content) > 500:
            result["homepage"] = content
            print(f"  ✅ Homepage — {len(content)} chars")
        else:
            print("  ⚠️ Homepage too weak")

    except Exception as e:
        print(f"  ❌ Homepage failed: {e}")

    # -------------------------
    # 2. CAREERS
    # -------------------------
    possible_paths = [
        "/careers",
        "/jobs",
        "/company/careers",
        "/join-us",
        "/work-with-us"
    ]

    for path in possible_paths:
        jobs_url = url.rstrip("/") + path
        try:
            print(f"  🔹 Trying jobs: {jobs_url}")

            res = app.crawl(jobs_url, limit=3)

            pages = []
            if isinstance(res, dict):
                pages = res.get("data", [])
            elif hasattr(res, "data"):
                pages = res.data

            combined = ""
            for page in pages:
                if isinstance(page, dict):
                    combined += page.get("markdown", "")

            if len(combined) > 800 and any(word in combined.lower() for word in ["job", "role", "position", "apply"]):
                result["jobs"] = combined
                print(f"  ✅ Jobs found (crawl)")
                break

            # fallback
            res = app.scrape(jobs_url, formats=["markdown"])
            content = extract_markdown_safe(res)

            if content and len(content) > 500:
                result["jobs"] = content
                print(f"  ✅ Jobs found (scrape)")
                break

        except Exception as e:
            print(f"  ❌ Failed {jobs_url}: {e}")
            continue

    # -------------------------
    # 3. NEWS
    # -------------------------
    try:
        from tavily import TavilyClient
        print("  🔹 Searching news...")

        tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        company_name = extract_company_name(url)

        queries = [
            f"{company_name} company latest news",
            f"{company_name} SaaS product updates",
            f"{company_name} acquisitions funding"
        ]

        news_set = set()
        news_texts = []

        for q in queries:
            search_result = tavily.search(query=q, max_results=2)

            for r in search_result.get("results", []):
                title = r.get("title", "")
                content = r.get("content", "")[:200]

                if title and title not in news_set:
                    news_set.add(title)
                    news_texts.append(f"- {title}: {content}")

        if news_texts:
            result["news"] = "\n".join(news_texts)
            print(f"  ✅ News collected")

    except Exception as e:
        print(f"  ❌ News failed: {e}")

    # -------------------------
    # SAVE FILE (IMPORTANT)
    # -------------------------
    output_path = "backend/data/prospect.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved prospect to {output_path}")

    return result


# -------------------------
# OPTIONAL DIRECT RUN
# -------------------------
if __name__ == "__main__":
    test_url = input("Enter URL: ")
    scrape_prospect(test_url)