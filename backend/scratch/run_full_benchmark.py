import asyncio
import os
import sys
import json

sys.path.insert(0, os.path.abspath("backend"))

from app.schemas.query import QueryRequest
from rag.pipeline import RAGPipeline

async def main():
    pipeline = RAGPipeline()
    results = []

    tests = [
        ("1. What is PMFBY?", "What is PMFBY?", "en", "sess-1"),
        ("2. पीएमएफबीवाय म्हणजे काय?", "पीएमएफबीवाय म्हणजे काय?", "mr", "sess-2"),
        ("3. माझे सोयाबीन पीक...", "माझे सोयाबीन पीक जास्त पावसामुळे खराब झाले आहे. आता काय करू?", "mr", "sess-3"),
        ("4. What services at PACS?", "What services are available at PACS?", "en", "sess-4"),
        ("5. PACS मध्ये सेवा...", "PACS मध्ये कोणत्या सेवा मिळतात?", "mr", "sess-5"),
        ("6. What is financial literacy?", "What is financial literacy?", "en", "sess-6"),
        ("7. आर्थिक साक्षरता म्हणजे काय?", "आर्थिक साक्षरता म्हणजे काय?", "mr", "sess-7"),
        ("8. What is MCS Act?", "What is the Maharashtra Cooperative Societies Act?", "en", "sess-8"),
        ("9. तक्रार कशी करावी?", "सहकारी संस्थेची तक्रार कशी करावी?", "mr", "sess-9"),
        ("10. Turn 1 PMFBY", "What is PMFBY?", "en", "sess-10"),
        ("10. Turn 2 Documents", "What documents do I need?", "en", "sess-10"),
        ("11. Registration Fee", "What is the exact registration fee for a cooperative society in 2026?", "en", "sess-11"),
    ]

    for label, query, lang, sess_id in tests:
        req = QueryRequest(message=query, language=lang, session_id=sess_id)
        try:
            resp, sources = await pipeline.process_query(req)
            src_titles = [getattr(s, "title", s.get("title") if isinstance(s, dict) else "") for s in (resp.sources or [])]
            results.append({
                "test": label,
                "query": query,
                "intent": resp.intent,
                "grounding_status": resp.grounding_status,
                "authority_level": resp.authority_level,
                "sources": src_titles,
                "spoken_answer": resp.spoken_answer,
                "display_preview": resp.display_answer[:250] if resp.display_answer else ""
            })
        except Exception as exc:
            results.append({
                "test": label,
                "query": query,
                "error": str(exc)
            })

    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
