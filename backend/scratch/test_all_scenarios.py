import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("backend"))

from app.schemas.query import QueryRequest
from rag.pipeline import RAGPipeline

async def main():
    pipeline = RAGPipeline()

    scenarios = [
        ("A. English PMFBY", "en", "My crop suffered excessive rain/inundation. What should I do under PMFBY?"),
        ("B. Hindi PMFBY", "hi", "बारिश से मेरी फसल खराब हो गई है। PMFBY के तहत मुझे क्या करना चाहिए?"),
        ("C. Marathi PMFBY", "mr", "अतिवृष्टीमुळे माझ्या पिकाचे नुकसान झाले आहे. PMFBY अंतर्गत मला काय करावे?"),
        ("D. PACS", "en", "What services can I get from a PACS?"),
        ("E. Cooperative Law", "en", "What is a cooperative by-law?"),
        ("F. Financial Literacy", "en", "How can a cooperative member improve financial literacy?"),
        ("G. Unrelated Query", "en", "Who is the Prime Minister of India?")
    ]

    print("=" * 80)
    print("EXECUTING ALL 7 REQUIRED PRODUCTION SCENARIO TESTS")
    print("=" * 80)

    for label, lang, query in scenarios:
        print(f"\n--- TEST {label} ({lang.upper()}) ---")
        print(f"User Query: '{query}'")
        req = QueryRequest(message=query, language=lang, session_id=f"session-{label.replace(' ', '_')}")
        resp, sources = await pipeline.process_query(req)

        print(f"Detected Intent: {resp.intent}")
        print(f"Language: {resp.language}")
        print(f"Primary Source: {resp.source}")
        print(f"Display Answer Length: {len(resp.display_answer or '')} chars")
        print(f"Spoken Answer Length: {len(resp.spoken_answer or '')} chars")
        print("--- SPOKEN ANSWER ---")
        print(resp.spoken_answer)
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
