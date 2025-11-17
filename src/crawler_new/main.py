import json

from firecrawl import Firecrawl
from pymongo import MongoClient
import os

# Athleten laden
with open("athletes.json", "r") as f:
    athletes = json.load(f)
names = [athlet["name"] for athlet in athletes]

topics = [
    "recent news",
    "fan reactions",
    "personal stories",
    "emotional interviews",
    "media analysis"
]

fc = Firecrawl(api_key=os.environ["FIRECRAWL_API_KEY"]) # Erwartet: export FIRECRAWL_API_KEY=sk_dein_key
mongo = MongoClient("mongodb://localhost:27017").crawler.firecrawl_results

for name in names:
    for topic in topics:
        query = f'{name} {topic}'
        print(f"Suche: {query}")
        raw = fc.search(query=query, limit=10, scrape_options={"formats": ["markdown", "links"]})

        items = raw.get("results") if isinstance(raw, dict) and "results" in raw else (
            raw if isinstance(raw, list) else [raw])
        items = [i if isinstance(i, dict) else getattr(i, "model_dump", lambda: getattr(i, "__dict__", {}))() for i in
                 items]

        for i in items:
            i["athlete_name"] = name
            i["topic"] = topic

        mongo.insert_many(items)


# raw = fc.search(
#     query="Short track speed skating 500m race strategy and overtaking tactics analysis",
#     limit=1,
#     scrape_options={"formats": ["markdown", "links"]}
# )
# # Normalisierung auf Liste von dicts (kompatibel für insert_many)
# items = raw.get("results") if isinstance(raw, dict) and "results" in raw else (raw if isinstance(raw, list) else [raw])
# items = [i if isinstance(i, dict) else getattr(i, "model_dump", lambda: getattr(i, "__dict__", {}))() for i in items]
# MongoClient("mongodb://admin:admin@localhost:27017/?authSource=admin").crawler.firecrawl_results.insert_many(items)

