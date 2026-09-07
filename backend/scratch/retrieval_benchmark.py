import asyncio
import os
import sys
import json

sys.path.insert(0, os.path.abspath("backend"))

from rag.intent import classify_intent, extract_topic_and_goal
from rag.retriever import retrieve_relevant_knowledge
from rag.web_search import search_web_knowledge

BENCHMARK_QUERIES = [
    ("1. What is PMFBY?", "What is PMFBY?", "en"),
    ("2. माझे सोयाबीन पीक जास्त पावसामुळे खराब झाले आहे. आता काय करू?", "माझे सोयाबीन पीक जास्त पावसामुळे खराब झाले आहे. आता काय करू?", "mr"),
    ("3. PACS मध्ये कोणत्या सेवा मिळतात?", "PACS मध्ये कोणत्या सेवा मिळतात?", "mr"),
    ("4. What is financial literacy?", "What is financial literacy?", "en"),
    ("5. सहकारी संस्थेची तक्रार कशी करावी?", "सहकारी संस्थेची तक्रार कशी करावी?", "mr"),
    ("6. What is the Maharashtra Cooperative Societies Act?", "What is the Maharashtra Cooperative Societies Act?", "en"),
    ("7. What services are available at PACS?", "What services are available at PACS?", "en"),
    ("8. Tr maza soyabeen peek hot tr te jast pausa ni kharab zal ata kay karu", "Tr maza soyabeen peek hot tr te jast pausa ni kharab zal ata kay karu", "mr"),
    ("9. What is the exact registration fee for a cooperative society?", "What is the exact registration fee for a cooperative society?", "en"),
]

def run_retrieval_benchmark():
    results = []
    for label, query, lang in BENCHMARK_QUERIES:
        intent = classify_intent(query)
        topic, goal = extract_topic_and_goal(query)
        rag_chunks = retrieve_relevant_knowledge(query, lang, intent, top_k=4, match_threshold=0.4)
        web_res = search_web_knowledge(query, max_results=3)

        chunk_details = [
            {
                "title": c.get("title"),
                "source_name": c.get("source_name"),
                "similarity": c.get("similarity"),
                "document_id": c.get("document_id")
            }
            for c in rag_chunks
        ]

        web_details = [
            {
                "title": w.get("title"),
                "source_url": w.get("source_url"),
                "authority_level": w.get("authority_level")
            }
            for w in web_res
        ]

        results.append({
            "label": label,
            "query": query,
            "language": lang,
            "intent": intent,
            "topic": topic,
            "goal": goal,
            "rag_chunk_count": len(rag_chunks),
            "rag_chunks": chunk_details,
            "web_source_count": len(web_res),
            "web_sources": web_details
        })

    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    run_retrieval_benchmark()
