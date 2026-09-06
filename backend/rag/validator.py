"""
Factual Grounding & Source Validation Module for SahkaarSetu (SIH26088).

Enforces strict factual accuracy and source validation BEFORE responses are delivered:
1. Strips invalid claims (e.g. PMFBY mandatory claims, 100% coverage claims, unverified percentage numbers).
2. Filters out Wikipedia/generic non-authoritative sources for government/legal queries.
3. Classifies sources into Tier 1 OFFICIAL_GOVERNMENT, Tier 2 INSTITUTIONAL, Tier 3 GENERAL.
4. Attaches structured source metadata with retrieved_at timestamp and authority_level.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

# Tier 1 Official Government & Regulatory Domain Patterns
OFFICIAL_GOV_DOMAINS = [
    "cooperation.gov.in",
    "pmfby.gov.in",
    "mahadbt.maharashtra.gov.in",
    "agri.maharashtra.gov.in",
    "agri.gov.in",
    "pib.gov.in",
    "nabard.org",
    "rbi.org.in",
    "myscheme.gov.in",
    "india.gov.in",
    "gov.in",
    "nic.in",
]


def classify_source_authority(url: str, source_name: str = "") -> str:
    """Classify source into Tier 1 OFFICIAL_GOVERNMENT, Tier 2 INSTITUTIONAL, or Tier 3 GENERAL."""
    target = f"{url} {source_name}".lower()
    if any(domain in target for domain in OFFICIAL_GOV_DOMAINS):
        return "OFFICIAL_GOVERNMENT"
    if any(term in target for term in ["bank", "dccb", "ncui", "cooperative federation", "society"]):
        return "INSTITUTIONAL"
    return "GENERAL"


def sanitize_source_citations(raw_sources: List[Dict[str, Any]], is_legal_or_gov_query: bool = True) -> List[Dict[str, Any]]:
    """
    Filters and formats source metadata.
    Excludes Wikipedia and non-authoritative general blogs for legal/government queries.
    Attaches title, organization, url, retrieved_at timestamp, and authority_level.
    """
    sanitized: List[Dict[str, Any]] = []
    seen_urls = set()
    current_iso_time = datetime.now(timezone.utc).isoformat()

    for item in raw_sources:
        url = item.get("source_url") or item.get("url") or ""
        url_lower = url.lower()

        # Reject Wikipedia or generic non-government blogs for official government/legal queries
        if is_legal_or_gov_query:
            if "wikipedia.org" in url_lower or "blogspot.com" in url_lower or "wordpress.com" in url_lower:
                logger.info(f"[SOURCE FILTER] Stripped non-authoritative source: {url}")
                continue

        authority = item.get("authority_level") or classify_source_authority(url, item.get("source_name", ""))
        title = item.get("title") or "Official Guidance"
        org = item.get("source_name") or item.get("organization") or "Government Portal"

        dedup_key = f"{title}-{url}".lower()
        if dedup_key in seen_urls:
            continue
        seen_urls.add(dedup_key)

        sanitized.append({
            "title": title,
            "source_name": org,
            "organization": org,
            "source_url": url,
            "url": url,
            "document_id": item.get("document_id"),
            "authority_level": authority,
            "retrieved_at": current_iso_time,
        })

    # Sort Tier 1 (OFFICIAL_GOVERNMENT) first
    sanitized.sort(key=lambda s: 0 if s["authority_level"] == "OFFICIAL_GOVERNMENT" else 1)
    return sanitized


def validate_and_sanitize_claims(
    raw_answer: str,
    language: str,
    intent: str,
    grounding_context: str = "",
) -> Tuple[str, bool, List[str]]:
    """
    Validates factual claims in generated answer against grounded knowledge rules:
    - Replaces false claims that PMFBY is mandatory.
    - Replaces false claims of 100% crop insurance coverage.
    - Replaces unverified fixed percentage subsidy numbers in tractor queries.

    Returns (sanitized_answer, is_valid, list_of_corrected_claims).
    """
    if not raw_answer:
        return "", True, []

    ans = raw_answer
    corrected_claims: List[str] = []

    # -------------------------------------------------------------------------
    # Rule 1: PMFBY Mandatory Claim Correction
    # PMFBY has been voluntary for all farmers (including loanee) since Kharif 2020.
    # -------------------------------------------------------------------------
    mandatory_patterns = [
        (r"(?:pmfby|पीक\s*विमा|फसल\s*बीमा|crop\s*insurance)[^.\n]*?(?:mandatory|compulsory|अनिवार्य|अपरिहार्य)",
         "PMFBY_CLAIM_MANDATORY_VIOLATION"),
        (r"अनिवार्य\s*(?:आहे|है|होगा)", "PMFBY_CLAIM_MANDATORY_VIOLATION_WORD"),
    ]

    for pattern, violation_tag in mandatory_patterns:
        if re.search(pattern, ans, re.IGNORECASE):
            logger.warning(f"[FACTUAL VALIDATOR] Correcting unsupported claim: {violation_tag}")
            corrected_claims.append(f"Removed claim that PMFBY is mandatory (PMFBY is voluntary since 2020).")

            if language == "mr":
                ans = re.sub(
                    r"सर्व\s*शेतकऱ्यांसाठी\s*अनिवार्य\s*(?:आहे|राहील)",
                    "सर्व शेतकऱ्यांसाठी ऐच्छिक (Voluntary) आहे",
                    ans,
                    flags=re.IGNORECASE,
                )
                ans = re.sub(
                    r"अनिवार्य\s*आहे",
                    "ऐच्छिक (Voluntary) आहे",
                    ans,
                    flags=re.IGNORECASE,
                )
            elif language == "hi":
                ans = re.sub(
                    r"सभी\s*किसानों\s*के\s*लिए\s*अनिवार्य\s*(?:है|होगा)",
                    "सभी किसानों के लिए ऐच्छिक (Voluntary) है",
                    ans,
                    flags=re.IGNORECASE,
                )
                ans = re.sub(
                    r"अनिवार्य\s*है",
                    "ऐच्छिक (Voluntary) है",
                    ans,
                    flags=re.IGNORECASE,
                )
            else:
                ans = re.sub(
                    r"mandatory\s*for\s*all\s*farmers",
                    "voluntary for all farmers",
                    ans,
                    flags=re.IGNORECASE,
                )
                ans = re.sub(
                    r"is\s*mandatory",
                    "is a voluntary crop insurance scheme",
                    ans,
                    flags=re.IGNORECASE,
                )

    # -------------------------------------------------------------------------
    # Rule 2: 100% Crop Insurance Coverage Claim Correction
    # Claim payouts depend on sum insured & yield shortfall assessment.
    # -------------------------------------------------------------------------
    coverage_patterns = [
        (r"100%\s*(?:coverage|कव्हरेज|भरपाई|कवरेज)", "100_PERCENT_COVERAGE_VIOLATION"),
        (r"१००%\s*(?:कव्हरेज|भरपाई|कवरेज)", "100_PERCENT_COVERAGE_VIOLATION_MR"),
    ]

    for pattern, violation_tag in coverage_patterns:
        if re.search(pattern, ans, re.IGNORECASE):
            logger.warning(f"[FACTUAL VALIDATOR] Correcting unsupported claim: {violation_tag}")
            corrected_claims.append("Removed claim of 100% coverage (Payout depends on sum insured and yield loss).")

            if language == "mr":
                ans = re.sub(
                    pattern,
                    "विहित विमा संरक्षण (Sum Insured) व पीक पाहणी पंचनाम्यानुसार भरपाई",
                    ans,
                    flags=re.IGNORECASE,
                )
            elif language == "hi":
                ans = re.sub(
                    pattern,
                    "बीमित राशि और फसल क्षति आकलन के आधार पर दावा भुगतान",
                    ans,
                    flags=re.IGNORECASE,
                )
            else:
                ans = re.sub(
                    pattern,
                    "coverage based on sum insured and yield loss assessment",
                    ans,
                    flags=re.IGNORECASE,
                )

    # -------------------------------------------------------------------------
    # Rule 3: Unverified Specific Subsidy Percentage in Tractor Queries
    # Do not invent fixed subsidy numbers like "25% subsidy" unless in context.
    # -------------------------------------------------------------------------
    if intent in {"MINISTRY_SCHEME", "AGRICULTURAL_SUPPORT"} or "tractor" in raw_answer.lower() or "ट्रॅक्टर" in raw_answer or "ट्रैक्टर" in raw_answer:
        # Check if percentage numbers exist in answer but NOT in grounding_context
        perc_matches = re.findall(r"\b(\d{1,2}%)\b", ans)
        for perc in perc_matches:
            if perc not in grounding_context:
                logger.warning(f"[FACTUAL VALIDATOR] Removing unverified subsidy percentage '{perc}' not found in grounded context")
                corrected_claims.append(f"Removed unverified subsidy percentage '{perc}' (stated generally as per official scheme guidelines).")
                if language == "mr":
                    ans = ans.replace(f"{perc} अनुदान", "योजनेच्या नियमांनुसार अनुदान")
                    ans = ans.replace(f"{perc} सबसिडी", "शासकीय नियमांनुसार सबसिडी")
                    ans = ans.replace(f"{perc}", "शासकीय नियमानुसार")
                elif language == "hi":
                    ans = ans.replace(f"{perc} सब्सिडी", "सरकारी नियमानुसार सब्सिडी")
                    ans = ans.replace(f"{perc}", "नियमानुसार")
                else:
                    ans = ans.replace(f"{perc} subsidy", "subsidy as per official guidelines")
                    ans = ans.replace(f"{perc}", "as per guidelines")

    # -------------------------------------------------------------------------
    # Rule 4: Correct SMAM Terminology
    # Replaces invalid acronym expansions like "स्मॉल मॅकेनायझेशन" with official "कृषी यांत्रिकीकरण उप-अभियान (SMAM)".
    # -------------------------------------------------------------------------
    if "स्मॉल मॅकेनायझेशन" in ans or "small mechanisation" in ans.lower() or "small mechanization" in ans.lower():
        corrected_claims.append("Corrected SMAM acronym expansion to official title 'Sub-Mission on Agricultural Mechanization (SMAM)'.")
        if language == "mr":
            ans = ans.replace("स्मॉल मॅकेनायझेशन", "कृषी यांत्रिकीकरण उप-अभियान")
            ans = ans.replace("स्मॉल मॅकेनायझेशन (SMAM)", "कृषी यांत्रिकीकरण उप-अभियान (SMAM)")
        else:
            ans = re.sub(r"small\s+mechanisation|small\s+mechanization", "Sub-Mission on Agricultural Mechanization", ans, flags=re.IGNORECASE)

    is_valid = len(corrected_claims) == 0
    return ans, is_valid, corrected_claims


def evaluate_grounding_status(sources_list: List[Dict[str, Any]], claims_valid: bool = True) -> Tuple[str, str, bool]:
    """
    Evaluate grounding_status, overall authority_level, and claims_validated status.

    grounding_status:
      - VERIFIED: At least 1 Tier 1 OFFICIAL_GOVERNMENT source retrieved AND claims valid.
      - PARTIALLY_VERIFIED: Tier 2 INSTITUTIONAL sources retrieved.
      - UNVERIFIED: No official/institutional sources retrieved.
      - REFUSED_TO_GUESS: System explicitly refrained from inventing ungrounded factual numbers.

    authority_level:
      - OFFICIAL_GOVERNMENT
      - TRUSTED_INSTITUTION
      - SECONDARY
      - NONE

    Returns (grounding_status, authority_level, claims_validated).
    """
    if not sources_list:
        return "UNVERIFIED", "NONE", claims_valid

    has_official = any(s.get("authority_level") == "OFFICIAL_GOVERNMENT" for s in sources_list)
    has_inst = any(s.get("authority_level") == "INSTITUTIONAL" for s in sources_list)

    if has_official:
        auth_level = "OFFICIAL_GOVERNMENT"
        g_status = "VERIFIED" if claims_valid else "PARTIALLY_VERIFIED"
    elif has_inst:
        auth_level = "TRUSTED_INSTITUTION"
        g_status = "PARTIALLY_VERIFIED"
    else:
        auth_level = "SECONDARY"
        g_status = "UNVERIFIED"

    return g_status, auth_level, claims_valid

