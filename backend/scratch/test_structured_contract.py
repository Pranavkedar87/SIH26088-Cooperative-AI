import asyncio
import os
import sys

# Ensure backend directory is on python path
sys.path.insert(0, os.path.abspath("backend"))

from app.schemas.query import QueryRequest
from rag.pipeline import RAGPipeline

async def run_tests():
    pipeline = RAGPipeline()

    test_queries = [
        ("en", "Who is the Prime Minister of India?"),
        ("en", "What are the official PMFBY claim reporting steps after excessive rain or inundation?"),
        ("en", "What services are available through PACS?"),
        ("mr", "पीक नुकसानीनंतर पीक विमा भरपाईसाठी काय करावे?"),
        ("hi", "फसल क्षति रिपोर्टिंग और पीएमएफबीवाई दावों के लिए क्या प्रक्रिया है?")
    ]

    print("=" * 80)
    print("STARTING STRUCTURED RESPONSE CONTRACT TESTS")
    print("=" * 80)

    for idx, (lang, text) in enumerate(test_queries, 1):
        print(f"\n--- TEST QUERY #{idx} ({lang.upper()}) ---")
        print(f"User Query: {text}")
        req = QueryRequest(message=text, language=lang, session_id=f"test-session-{idx}")
        resp, sources = await pipeline.process_query(req)

        print(f"Status / Intent: {resp.intent}")
        print(f"Primary Source: {resp.source}")
        print(f"Display Answer Length: {len(resp.display_answer or '')} chars")
        print(f"Spoken Answer Length: {len(resp.spoken_answer or '')} chars")

        print("\n--- DISPLAY ANSWER PREVIEW ---")
        print(resp.display_answer[:350])
        print("...")

        print("\n--- SPOKEN ANSWER PREVIEW ---")
        print(resp.spoken_answer)
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(run_tests())
