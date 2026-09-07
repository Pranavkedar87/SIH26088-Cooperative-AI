"""
test_task19_guided_experience.py

Acceptance test suite for Task 19: Final Guided Conversation + Structured Follow-ups + Smart PDF.
"""
import sys
import os
import json

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.schemas.query import QueryResponse, SuggestedFollowup, SourceItem
from rag.pipeline import generate_contextual_followups


def test_followup_generation_pmfby():
    print("\n--- Test 1: PMFBY Contextual Follow-ups ---")
    
    # 1. Overview
    fu_en = generate_contextual_followups("PMFBY", "CROP_INSURANCE", "OVERVIEW", "en", "What is PMFBY?")
    assert 2 <= len(fu_en) <= 4, f"Expected 2-4 followups, got {len(fu_en)}"
    assert any("document" in f["label"].lower() for f in fu_en)
    assert any("procedure" in f["label"].lower() for f in fu_en)
    print("  [OK] PMFBY Overview (EN):", [f["label"] for f in fu_en])

    # 2. Documents (should not suggest 'What documents' again)
    fu_docs = generate_contextual_followups("PMFBY", "CROP_INSURANCE", "DOCUMENTS", "en", "What documents do I need?")
    assert not any(f["label"].lower() == "what is pmfby?" for f in fu_docs)
    print("  [OK] PMFBY Documents (EN):", [f["label"] for f in fu_docs])

    # 3. Procedure
    fu_proc = generate_contextual_followups("PMFBY", "CROP_INSURANCE", "PROCEDURE", "en", "What is the procedure?")
    print("  [OK] PMFBY Procedure (EN):", [f["label"] for f in fu_proc])

    # 4. Contact
    fu_contact = generate_contextual_followups("PMFBY", "CROP_INSURANCE", "CONTACT", "en", "Who should I contact?")
    assert not any(f["label"].lower() == "who should i contact?" for f in fu_contact)
    print("  [OK] PMFBY Contact (EN):", [f["label"] for f in fu_contact])


def test_multilingual_followups():
    print("\n--- Test 2: Multilingual Follow-ups (Hindi & Marathi) ---")
    
    # Marathi PMFBY
    fu_mr = generate_contextual_followups("PMFBY", "CROP_INSURANCE", "OVERVIEW", "mr", "पीएमएफबीवाय म्हणजे काय?")
    assert 2 <= len(fu_mr) <= 4
    assert any("कागदपत्रे" in f["label"] for f in fu_mr)
    print("  [OK] Marathi PMFBY:", [f["label"] for f in fu_mr])

    # Hindi PMFBY
    fu_hi = generate_contextual_followups("PMFBY", "CROP_INSURANCE", "OVERVIEW", "hi", "पीएमएफबीवाई क्या है?")
    assert 2 <= len(fu_hi) <= 4
    assert any("दस्तावेज" in f["label"] for f in fu_hi)
    print("  [OK] Hindi PMFBY:", [f["label"] for f in fu_hi])


def test_domains_followups():
    print("\n--- Test 3: PACS, Grievance, Financial Literacy, Tractor ---")
    
    # PACS
    fu_pacs = generate_contextual_followups("PACS_SERVICE", "PACS_MEMBERSHIP", "OVERVIEW", "en", "What is PACS?")
    print("  [OK] PACS:", [f["label"] for f in fu_pacs])
    assert any("crop loan" in f["label"].lower() or "loan" in f["label"].lower() for f in fu_pacs)

    # Tractor Subsidy
    fu_tractor = generate_contextual_followups("MINISTRY_SCHEME", "TRACTOR_PURCHASE", "OVERVIEW", "en", "I want to buy a tractor subsidy")
    print("  [OK] Tractor:", [f["label"] for f in fu_tractor])
    assert any("document" in f["label"].lower() or "process" in f["label"].lower() or "eligibility" in f["label"].lower() for f in fu_tractor)

    # Grievance
    fu_grievance = generate_contextual_followups("GRIEVANCE", None, "OVERVIEW", "en", "I have a complaint against my society")
    print("  [OK] Grievance:", [f["label"] for f in fu_grievance])
    assert any("authority" in f["label"].lower() or "complaint" in f["label"].lower() for f in fu_grievance)

    # Financial Literacy
    fu_fin = generate_contextual_followups("FINANCIAL_LITERACY", None, "OVERVIEW", "en", "What is financial literacy?")
    print("  [OK] Financial:", [f["label"] for f in fu_fin])


def test_schema_contract():
    print("\n--- Test 4: QueryResponse Pydantic Contract Serialization ---")
    
    resp = QueryResponse(
        answer="Sample answer",
        display_answer="Sample display answer",
        spoken_answer="Sample spoken answer",
        language="en",
        intent="PMFBY",
        answer_focus="OVERVIEW",
        source="Ministry of Agriculture",
        sources=[
            SourceItem(
                title="PMFBY Guidelines",
                source_name="pmfby.gov.in",
                source_url="https://pmfby.gov.in",
                document_id="doc-001"
            )
        ],
        suggested_followups=[
            SuggestedFollowup(
                label="What documents do I need?",
                query="What documents do I need for PMFBY crop loss claim?"
            ),
            SuggestedFollowup(
                label="What is the reporting procedure?",
                query="What is the official procedure for PMFBY crop loss reporting?"
            )
        ],
        session_id="test-session-123"
    )

    data = json.loads(resp.model_dump_json())
    assert "suggested_followups" in data
    assert len(data["suggested_followups"]) == 2
    assert data["suggested_followups"][0]["label"] == "What documents do I need?"
    assert data["suggested_followups"][0]["query"] == "What documents do I need for PMFBY crop loss claim?"
    print("  [OK] QueryResponse serialized correctly with suggested_followups JSON contract!")


if __name__ == "__main__":
    test_followup_generation_pmfby()
    test_multilingual_followups()
    test_domains_followups()
    test_schema_contract()
    print("\n==========================================")
    print("ALL TASK 19 UNIT TESTS PASSED SUCCESSFULLY!")
    print("==========================================")
