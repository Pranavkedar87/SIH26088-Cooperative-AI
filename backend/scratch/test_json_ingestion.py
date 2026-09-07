import json
import os
import sys

sys.path.insert(0, os.path.abspath("backend"))

from rag.pipeline import extract_json_payload, clean_speech_text, generate_structured_answer

mock_gemini_nested_json = """{
  "display_answer": {
    "title": "PMFBY Crop Loss Intimation & Claim Process",
    "summary": "If your crop is damaged due to excessive rain or inundation, report the loss within 72 hours to your insurance company or local agriculture officer.",
    "what_should_i_do_now": [
      {
        "title": "Loss Intimation Procedure",
        "content": "Intimate crop damage within 72 hours via the Crop Insurance App, official toll-free helpline, or your local bank branch/agriculture office."
      },
      {
        "title": "Required Documents & Proofs",
        "content": "Keep 7/12 land extract, Aadhaar card, bank passbook, sowing certificate, and photos of damaged fields ready."
      },
      {
        "title": "Helpline & Follow-up Details",
        "content": "Contact your district agriculture officer, bank branch, or the insurer's toll-free helpline for joint field survey details."
      }
    ],
    "detailed_information": "Under Pradhan Mantri Fasal Bima Yojana (PMFBY), localized calamities such as inundation, landslide, and unseasonal rainfall are covered. Intimation within 72 hours is crucial for individual assessment. Post assessment, eligible claims are directly credited to the farmer's Aadhaar-linked bank account.",
    "next_guidance": "Would you like the contact helpline numbers or document checklist for your district?"
  },
  "spoken_answer": "If your crop is damaged due to excessive rain, intimate your insurance company or agriculture officer within 72 hours through the Crop Insurance App or toll-free helpline. Keep your land records and bank passbook ready."
}"""

payload = extract_json_payload(mock_gemini_nested_json)
assert payload is not None
print("1. Nested JSON Extraction Passed!")
disp = payload["display_answer"]
print("Title:", disp["title"])
print("Summary:", disp["summary"])
print("What Should I Do Now Count:", len(disp["what_should_i_do_now"]))
print("Spoken Answer:", clean_speech_text(payload["spoken_answer"]))

print("\nALL CANONICAL SCHEMA CHECKS PASSED SUCCESSFULLY!")
