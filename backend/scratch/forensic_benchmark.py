import asyncio
import os
import sys
import json

sys.path.insert(0, os.path.abspath("backend"))

from app.schemas.query import QueryRequest
from rag.pipeline import RAGPipeline

BENCHMARK_QUERIES = [
    ("A. PMFBY", "What is PMFBY?", "en"),
    ("B. PMFBY Marathi", "पीएमएफबीवाय म्हणजे काय?", "mr"),
    ("C. Crop support", "Tr maza soyabeen peek hot tr te jast pausa ni kharab zal ata kay karu", "mr"),
    ("D. PACS", "What services are available at PACS?", "en"),
    ("E. PACS Marathi", "PACS मध्ये कोणत्या सेवा मिळतात?", "mr"),
    ("F. Financial literacy", "What is financial literacy?", "en"),
    ("G. Cooperative law", "What is the Maharashtra Cooperative Societies Act?", "en"),
    ("H. Grievance", "सहकारी संस्थेची तक्रार कशी करावी?", "mr"),
    ("I. Unknown", "What is the exact registration fee for a cooperative society?", "en"),
]

async def run_benchmark():
    pipeline = RAGPipeline()
    results = []

    for label, query, lang in BENCHMARK_QUERIES:
        req = QueryRequest(message=query, language=lang, session_id=f"forensic-{label.replace(' ', '_')}")
        try:
            resp, sources = await pipeline.process_query(req)
            res_entry = {
                "label": label,
                "query": query,
                "language": lang,
                "intent": resp.intent,
                "grounding_status": resp.grounding_status,
                "authority_level": resp.authority_level,
                "source": resp.source,
                "sources_count": len(resp.sources or []),
                "source_titles": [getattr(s, "title", s.get("title") if isinstance(s, dict) else "") for s in (resp.sources or [])],
                "spoken_answer": resp.spoken_answer,
                "answer_preview": resp.display_answer[:300] if resp.display_answer else "",
            }
            results.append(res_entry)
        except Exception as exc:
            results.append({
                "label": label,
                "query": query,
                "error": str(exc)
            })

    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(run_benchmark())
