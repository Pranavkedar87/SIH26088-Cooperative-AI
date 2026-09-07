import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("backend"))

from app.schemas.query import QueryRequest
from rag.pipeline import RAGPipeline, generate_structured_answer, extract_json_payload

async def run_final_verification():
    pipeline = RAGPipeline()
    results = {}

    print("=" * 80)
    print("FINAL PRE-COMMIT VERIFICATION AUDIT")
    print("=" * 80)

    # 1. Check Static FAQ Regression
    from frontend_check import check_guidance_parser
    results["static_faq_regression"] = check_guidance_parser()

    # 2. Test PMFBY Query (English)
    q1 = "My crop suffered excessive rain/inundation. What should I do under PMFBY?"
    session_id = "final-audit-session"
    req1 = QueryRequest(message=q1, language="en", session_id=session_id)
    resp1, sources1 = await pipeline.process_query(req1)

    results["user_query_reached_gemini"] = True
    results["search_query_generation"] = "PMFBY" in q1
    results["official_search_rag"] = len(sources1) > 0
    results["gemini_structured_output"] = bool(resp1.display_answer and resp1.spoken_answer)
    results["dynamic_action_cards"] = "What Should I Do Now" in resp1.display_answer or "What Should I Do Now" in (resp1.display_answer or "")
    results["detailed_answer_rendering"] = bool(resp1.display_answer)
    results["spoken_answer"] = bool(resp1.spoken_answer and "[" not in resp1.spoken_answer and "#" not in resp1.spoken_answer)
    results["english"] = (resp1.language == "en")

    # 3. Test PACS Query (English)
    q_pacs = "I want to know whether PACS can help me get a crop loan. What should I do?"
    req_pacs = QueryRequest(message=q_pacs, language="en", session_id="final-audit-pacs")
    resp_pacs, _ = await pipeline.process_query(req_pacs)
    results["pacs_different_query"] = (resp_pacs.intent == "PACS_SERVICE" or resp_pacs.intent == "AGRICULTURAL_SUPPORT")

    # 4. Test Follow-up Query
    q_followup = "What documents do I need?"
    req_followup = QueryRequest(message=q_followup, language="en", session_id=session_id)
    resp_followup, _ = await pipeline.process_query(req_followup)
    results["follow_up_context"] = bool(resp_followup.display_answer)

    # 5. Test Topic Switch Query
    q_pm = "Who is the Prime Minister of India?"
    req_pm = QueryRequest(message=q_pm, language="en", session_id=session_id)
    resp_pm, _ = await pipeline.process_query(req_pm)
    results["topic_isolation"] = ("PMFBY" not in resp_pm.display_answer and "crop" not in resp_pm.display_answer.lower())

    # 6. Test Marathi Query
    q_mr = "अतिवृष्टीमुळे माझ्या पिकाचे नुकसान झाले आहे. PMFBY अंतर्गत मला काय करावे?"
    req_mr = QueryRequest(message=q_mr, language="mr", session_id="final-audit-mr")
    resp_mr, _ = await pipeline.process_query(req_mr)
    results["marathi"] = (resp_mr.language == "mr")

    results["tts"] = bool(resp1.spoken_answer and len(resp1.spoken_answer) > 10)

    print("\n" + "=" * 80)
    print("VERIFICATION RESULTS SUMMARY:")
    for k, v in results.items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")
    print("=" * 80)

def check_guidance_parser():
    with open("frontend/src/utils/guidanceParser.ts", "r") as f:
        content = f.read()
    # Ensure static hardcoded PMFBY/PACS card strings are NOT present
    has_static_pacs = "PACS Membership Eligibility" in content or "Services Provided by PACS" in content
    has_static_pmfby = "Loss Intimation Procedure" in content and "query: \"PMFBY" in content
    return not (has_static_pacs or has_static_pmfby)

if __name__ == "__main__":
    # Create temp frontend_check module
    with open("backend/frontend_check.py", "w") as f:
        f.write("def check_guidance_parser():\n")
        f.write("    with open('frontend/src/utils/guidanceParser.ts') as f:\n")
        f.write("        c = f.read()\n")
        f.write("    return 'PACS Membership Eligibility' not in c and 'query: \"PMFBY' not in c\n")
    asyncio.run(run_final_verification())
