"""
Manual Live API Test for POST /api/vision/analyze with a sample non-sensitive PMFBY document image.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from app.main import app


def create_sample_pmfby_image() -> bytes:
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    lines = [
        ("GOVERNMENT OF INDIA - MINISTRY OF AGRICULTURE", 30, (18, 59, 93)),
        ("PRADHAN MANTRI FASAL BIMA YOJANA (PMFBY)", 60, (15, 107, 104)),
        ("CROP INSURANCE ENROLLMENT ACKNOWLEDGEMENT SLIP", 90, (0, 0, 0)),
        ("-" * 70, 110, (150, 150, 150)),
        ("Season: Kharif 2024", 140, (0, 0, 0)),
        ("Farmer Name: Ramesh Patil", 170, (0, 0, 0)),
        ("Crop Name: Soyabean (सोयाबीन)", 200, (0, 0, 0)),
        ("Insured Area: 2.0 Hectares", 230, (0, 0, 0)),
        ("Sum Insured: INR 90,000", 260, (0, 0, 0)),
        ("Farmer Share Premium: INR 1,800 (Paid)", 290, (0, 0, 0)),
        ("Application Reference: PMFBY-MH-2024-KHARIF-00921", 320, (0, 0, 0)),
        ("Primary Cooperative: Dindori Taluka PACS, Nashik, Maharashtra", 350, (0, 0, 0)),
        ("Date of Receipt: 18 July 2024", 380, (0, 0, 0)),
        ("-" * 70, 410, (150, 150, 150)),
        ("IMPORTANT NOTICE TO INSURED FARMER:", 440, (197, 48, 48)),
        ("In case of localized crop damage due to heavy rainfall or inundation,", 470, (0, 0, 0)),
        ("intimate crop loss within 72 hours via Crop Insurance App or PACS.", 500, (0, 0, 0)),
        ("Toll-Free Helpline: 1800-200-5142", 530, (18, 59, 93)),
    ]

    for text, y, col in lines:
        draw.text((40, y), text, fill=col)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def test_live_vision_analyze():
    print("Generating synthetic non-sensitive PMFBY crop insurance slip...")
    image_bytes = create_sample_pmfby_image()
    print(f"Generated test JPEG ({len(image_bytes)} bytes)")

    client = TestClient(app)
    print("\nSending POST /api/vision/analyze...")
    response = client.post(
        "/api/vision/analyze",
        files={"file": ("pmfby_sample.jpg", io.BytesIO(image_bytes), "image/jpeg")},
        data={"language": "mr"},
    )

    print(f"Response Status: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    data = response.json()
    print("\nStructured Response JSON:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    # Validations
    assert data["success"] is True
    assert data["document_type"] == "PMFBY_POLICY", f"Unexpected doc_type: {data['document_type']}"
    assert data["readability"] in ["CLEAR", "BLURRY", "CROPPED", "POOR_LIGHTING"]
    assert "key_fields" in data and isinstance(data["key_fields"], dict)
    assert "document_summary" in data and data["document_summary"]
    assert "suggested_questions" in data and len(data["suggested_questions"]) > 0

    print("\n" + "=" * 60)
    print("MANUAL LIVE API TEST PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    test_live_vision_analyze()
