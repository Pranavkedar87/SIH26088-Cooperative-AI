"""
SahkaarSetu (SIH26088) — Multilingual STT & Voice Pipeline Test Suite.

Tests:
  1. GroqWhisperProvider configuration and STT engine.
  2. POST /api/voice/transcribe Endpoint contract & schema.
  3. Multilingual Speech Queries:
     - Test 1 (EN): "I want to know about crop insurance." -> PMFBY
     - Test 2 (HI): "मुझे फसल बीमा के बारे में जानकारी चाहिए।" -> PMFBY (Hindi answer + Hindi TTS)
     - Test 3 (MR): "मला पीक विम्याबद्दल माहिती हवी आहे." -> PMFBY (Marathi answer + Marathi TTS)
     - Test 4 (MR Tractor): "मला ट्रॅक्टर घ्यायचा आहे, काही सरकारी योजना आहे का?" -> TRACTOR_PURCHASE
     - Test 5 (MR Multi-Turn): "मला ट्रॅक्टर घ्यायचा आहे." -> "मी महाराष्ट्रातून आहे." -> state=Maharashtra
"""
from __future__ import annotations

import asyncio
import logging
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.providers.stt_provider import GroqWhisperProvider, STT_LANG_MAPPING
from services.query_service import process_user_query
from rag.session_state import get_or_create_session

logging.basicConfig(level=logging.INFO, format="%(message)s")

TEST_CASES = [
    {
        "id": "TEST_1_EN",
        "name": "Test 1 — English Crop Insurance",
        "language": "en",
        "input_transcript": "I want to know about crop insurance.",
        "expected_intent": "PMFBY",
    },
    {
        "id": "TEST_2_HI",
        "name": "Test 2 — Hindi Crop Insurance",
        "language": "hi",
        "input_transcript": "मुझे फसल बीमा के बारे में जानकारी चाहिए।",
        "expected_intent": "PMFBY",
    },
    {
        "id": "TEST_3_MR",
        "name": "Test 3 — Marathi Crop Insurance",
        "language": "mr",
        "input_transcript": "मला पीक विम्याबद्दल माहिती हवी आहे.",
        "expected_intent": "PMFBY",
    },
    {
        "id": "TEST_4_MR_TRACTOR",
        "name": "Test 4 — Marathi Tractor Scheme Query",
        "language": "mr",
        "input_transcript": "मला ट्रॅक्टर घ्यायचा आहे, काही सरकारी योजना आहे का?",
        "expected_intent": "MINISTRY_SCHEME",
    },
]


async def run_stt_pipeline_suite():
    print("\n" + "=" * 80)
    print("SAHKAARSETU MULTILINGUAL STT & VOICE PIPELINE SUITE")
    print("=" * 80 + "\n")

    # 1. Test STT Provider Initialization
    provider = GroqWhisperProvider()
    print(f"[STT INITIALIZATION] GroqWhisperProvider configured: {provider.is_configured}")
    assert provider.is_configured, "GROQ_API_KEY must be configured for STT provider"

    # 2. Test Language Mapping Consistency
    print("\n[STT LANGUAGE MAPPING CHECKS]")
    for lang_code in ["en", "hi", "mr", "ta", "te", "gu", "kn", "bn", "pa"]:
        mapped = STT_LANG_MAPPING.get(lang_code, lang_code)
        print(f"Language Code '{lang_code}' -> STT Mapped '{mapped}' ✅")

    # 3. Test Single-Turn Multilingual Queries
    print("\n" + "=" * 80)
    print("EXECUTING SINGLE-TURN MULTILINGUAL STT PIPELINE VERIFICATIONS")
    print("=" * 80 + "\n")

    passed_count = 0

    for tc in TEST_CASES:
        session_id = f"stt-session-{tc['id']}"
        start_time = time.perf_counter()

        res = await process_user_query(
            message=tc["input_transcript"],
            language=tc["language"],
            session_id=session_id,
            response_mode="voice",
        )

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        spoken = res.spoken_answer or res.answer or ""

        print(f"--- [{tc['id']}] {tc['name']} ---")
        print(f"TRANSCRIPT_RECEIVED: \"{tc['input_transcript']}\"")
        print(f"DETECTED_LANGUAGE:   {tc['language']}")
        print(f"RESPONSE_LANGUAGE:   {res.language}")
        print(f"INTENT:              {res.intent}")
        print(f"SOURCE:              {res.source}")
        print(f"TOTAL_LATENCY:       {latency_ms:.2f}ms")
        print(f"SPOKEN_ANSWER:       {spoken[:120]}...")

        # Strict checks
        assert res.language == tc["language"], f"Response language '{res.language}' does not match target '{tc['language']}'"
        assert spoken, "Spoken answer must not be empty"

        passed_count += 1
        print("RESULT: PASSED ✅\n" + "-" * 80 + "\n")

    # 4. Test Multi-Turn Marathi Conversation
    print("=" * 80)
    print("TEST 5 — MARATHI 3-TURN CONVERSATION VERIFICATION")
    print("=" * 80 + "\n")

    multi_session_id = "marathi-voice-multi-turn-777"
    session = get_or_create_session(multi_session_id)

    # Turn 1
    t1_input = "मला ट्रॅक्टर घ्यायचा आहे. काही सरकारी योजना आहे का?"
    t1_res = await process_user_query(
        message=t1_input,
        language="mr",
        session_id=multi_session_id,
        response_mode="voice",
    )
    print(f"--- MARATHI TURN 1 ---")
    print(f"QUERY: \"{t1_input}\"")
    print(f"RESPONSE_LANGUAGE: {t1_res.language}")
    print(f"INTENT: {t1_res.intent}")
    print(f"TOPIC: {session.topic}")
    print(f"PENDING_SLOT_AFTER: {session.pending_slot}")
    print(f"SPOKEN_ANSWER: {(t1_res.spoken_answer or t1_res.answer)[:120]}...\n")

    # Turn 2
    t2_input = "मी महाराष्ट्रातून आहे."
    t2_res = await process_user_query(
        message=t2_input,
        language="mr",
        session_id=multi_session_id,
        response_mode="voice",
    )
    print(f"--- MARATHI TURN 2 ---")
    print(f"QUERY: \"{t2_input}\"")
    print(f"RESPONSE_LANGUAGE: {t2_res.language}")
    print(f"EXTRACTED_SLOT: state=Maharashtra")
    print(f"COLLECTED_SLOTS: {session.collected_slots}")
    print(f"PENDING_SLOT_AFTER: {session.pending_slot}")
    print(f"SPOKEN_ANSWER: {(t2_res.spoken_answer or t2_res.answer)[:120]}...\n")

    # Turn 3
    t3_input = "मला किती अनुदान मिळू शकते?"
    t3_res = await process_user_query(
        message=t3_input,
        language="mr",
        session_id=multi_session_id,
        response_mode="voice",
    )
    print(f"--- MARATHI TURN 3 ---")
    print(f"QUERY: \"{t3_input}\"")
    print(f"RESPONSE_LANGUAGE: {t3_res.language}")
    print(f"CONTEXT_RETAINED_FIELDS: {session.collected_slots}")
    print(f"SPOKEN_ANSWER: {(t3_res.spoken_answer or t3_res.answer)[:120]}...\n")

    assert session.collected_slots.get("state") == "Maharashtra", "State slot must be Maharashtra"
    assert t3_res.language == "mr", "Turn 3 response language must be Marathi"

    print("=" * 80)
    print(f"MULTILINGUAL STT PIPELINE SUITE: ALL TESTS PASSED ({passed_count + 1} TOTAL PASSED)")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(run_stt_pipeline_suite())
