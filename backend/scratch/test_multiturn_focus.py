import asyncio
import os
import sys
import json

sys.path.insert(0, os.path.abspath("backend"))

from app.schemas.query import QueryRequest
from rag.pipeline import RAGPipeline

async def run_multiturn_tests():
    pipeline = RAGPipeline()
    session_id = "test-multiturn-session-100"

    print("=" * 80)
    print("RUNNING MULTI-TURN CONTEXT & ANSWER FOCUS VERIFICATION BENCHMARK")
    print("=" * 80)

    # 1. PMFBY Multi-turn Conversation
    turns = [
        ("Turn 1: Overview", "What is PMFBY?", "en"),
        ("Turn 2: Documents Focus", "What documents do I need?", "en"),
        ("Turn 3: Procedure Focus", "What is the official step-by-step procedure for this?", "en"),
        ("Turn 4: Contact Focus", "Who should I contact?", "en"),
        ("Turn 5: Context Reset", "Who is the Prime Minister of India?", "en"),
    ]

    for label, query, lang in turns:
        print(f"\n--- {label} ---")
        print(f"User Query: '{query}'")
        req = QueryRequest(message=query, language=lang, session_id=session_id)
        resp, _ = await pipeline.process_query(req)
        print(f"Intent: {resp.intent}")
        print(f"Spoken Answer: {resp.spoken_answer}")
        print(f"Display Answer Preview:\n{resp.display_answer[:300]}...")

    # 2. PACS Multi-turn Conversation
    pacs_session = "test-pacs-session-200"
    pacs_turns = [
        ("PACS Turn 1: Services", "PACS मध्ये कोणत्या सेवा मिळतात?", "mr"),
        ("PACS Turn 2: Next Step", "मला कर्जासाठी पुढे काय करावे?", "mr"),
    ]

    for label, query, lang in pacs_turns:
        print(f"\n--- {label} ---")
        print(f"User Query: '{query}'")
        req = QueryRequest(message=query, language=lang, session_id=pacs_session)
        resp, _ = await pipeline.process_query(req)
        print(f"Intent: {resp.intent}")
        print(f"Spoken Answer: {resp.spoken_answer}")
        print(f"Display Answer Preview:\n{resp.display_answer[:300]}...")

    # 3. Marathi Crop Damage Query
    mr_crop_session = "test-mr-crop-300"
    print(f"\n--- MARATHI CROP DAMAGE QUERY ---")
    q_mr = "माझे सोयाबीन पीक जास्त पावसामुळे खराब झाले आहे. आता काय करू?"
    print(f"User Query: '{q_mr}'")
    req = QueryRequest(message=q_mr, language="mr", session_id=mr_crop_session)
    resp, _ = await pipeline.process_query(req)
    print(f"Intent: {resp.intent}")
    print(f"Spoken Answer: {resp.spoken_answer}")
    print(f"Display Answer Preview:\n{resp.display_answer[:300]}...")

    print("\n=" * 80)
    print("ALL MULTI-TURN CONTEXT & ANSWER FOCUS TESTS COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_multiturn_tests())
