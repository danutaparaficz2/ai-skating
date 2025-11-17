from pymongo import MongoClient

db = MongoClient("mongodb://admin:admin@localhost:27017/?authSource=admin").crawler
count = db.firecrawl_results.count_documents({})
print(f"Anzahl Dokumente: {count}")

if count > 0:
    doc = db.firecrawl_results.find_one()
    print(f"\nErste Dokument Keys: {list(doc.keys())}")
    if 'title' in doc:
        print(f"Title: {doc['title']}")
    if 'url' in doc:
        print(f"URL: {doc['url']}")

