from firecrawl import FirecrawlApp
from dotenv import load_dotenv
import os
import json

load_dotenv()

app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

urls = [
    "https://igniteiq.ai/",
    "https://igniteiq.ai/services",
    "https://igniteiq.ai/products",
    "https://igniteiq.ai/solutions",
    "https://igniteiq.ai/portfolio",
]

print("Scraping IgniteIQ pages...")

all_chunks = []

for url in urls:
    try:
        print(f"  Scraping {url}")
        
        result = app.scrape(url, formats=["markdown"])

        # 🔥 FIX: result is a dict
        content = getattr(result, "markdown", None)

        if content:
            all_chunks.append({
                "source": url,
                "content": content
            })
            print(f"  Done — {len(content)} chars")
        else:
            print(f"  Empty response for {url}")

    except Exception as e:
        print(f"  Failed {url}: {e}")

output_path = "iq_scout/data/raw/igniteiq_scraped.json"

os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(all_chunks, f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(all_chunks)} pages to {output_path}")