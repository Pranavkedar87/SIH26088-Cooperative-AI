import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("backend"))

from app.schemas.query import QueryRequest
from rag.pipeline import RAGPipeline

async def main():
    pipeline = RAGPipeline()
    session_id = "test-architecture-session-1"

    print("=" * 80)
    print("TESTING USER-QUERY DRIVEN ARCHITECTURE & FOLLOW-UP CONTEXT")
    print("=" * 80)

    # 1. First query: Specific PMFBY crop damage query
    q1 = "My crop suffered excessive rain/inundation. What should I do under PMFBY?"
    print(f"\n--- TURN 1 ---")
    print(f"User Query: '{q1}'")
    req1 = QueryRequest(message=q1, language="en", session_id=session_id)
    resp1, _ = await pipeline.process_query(req1)
    print(f"Intent: {resp1.intent}")
    print(f"Spoken Answer: {resp1.spoken_answer}")
    print(f"Display Answer Preview:\n{resp1.display_answer[:300]}...")

    # 2. Turn 2: Follow-up query ("What documents do I need?")
    q2 = "What documents do I need?"
    print(f"\n--- TURN 2 (FOLLOW-UP) ---")
    print(f"User Query: '{q2}'")
    req2 = QueryRequest(message=q2, language="en", session_id=session_id)
    resp2, _ = await pipeline.process_query(req2)
    print(f"Intent: {resp2.intent}")
    print(f"Spoken Answer: {resp2.spoken_answer}")
    print(f"Display Answer Preview:\n{resp2.display_answer[:300]}...")

    # 4. Turn 4: Marathi Query ("माझ्या पिकाचे पावसामुळे नुकसान झाले आहे, मला काय करावे लागेल?")
    q4 = "माझ्या पिकाचे पावसामुळे नुकसान झाले आहे, मला काय करावे लागेल?"
    print(f"\n--- TURN 4 (MARATHI CROP DAMAGE QUERY) ---")
    print(f"User Query: '{q4}'")
    req4 = QueryRequest(message=q4, language="mr", session_id=session_id)
    resp4, _ = await pipeline.process_query(req4)
    print(f"Intent: {resp4.intent}")
    print(f"Spoken Answer: {resp4.spoken_answer}")
    print(f"Display Answer Preview:\n{resp4.display_answer[:300]}...")

    # 5. Turn 5: Explicit Domain Switch ("I want to buy a tractor under SMAM scheme")
    q5 = "I want to buy a tractor under SMAM scheme"
    print(f"\n--- TURN 5 (EXPLICIT DOMAIN SWITCH TO TRACTOR SCHEME) ---")
    print(f"User Query: '{q5}'")
    req5 = QueryRequest(message=q5, language="en", session_id=session_id)
    resp5, _ = await pipeline.process_query(req5)
    print(f"Intent: {resp5.intent}")
    print(f"Spoken Answer: {resp5.spoken_answer}")
    print(f"Display Answer Preview:\n{resp5.display_answer[:300]}...")

    print("\n=" * 80)
    print("ALL ARCHITECTURE & FOLLOW-UP TESTS EXECUTED SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
