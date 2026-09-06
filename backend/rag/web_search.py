"""
Authoritative Government Web Research Module for SahkaarSetu (SIH26088).

Performs live web research prioritizing official government and institutional portals:
  1. Primary: cooperation.gov.in, pib.gov.in, pmfby.gov.in, nabard.org, rbi.org.in, myscheme.gov.in, india.gov.in, *.gov.in, *.nic.in
  2. Authority Tagging: OFFICIAL_GOVERNMENT vs GENERAL
  3. Strict Sorting: Official government sources ALWAYS precede general/encyclopedic sources.
"""
from __future__ import annotations

import json
import logging
import re
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Trusted government and institutional domain patterns
GOVERNMENT_DOMAINS = [
    "cooperation.gov.in",
    "pib.gov.in",
    "pmfby.gov.in",
    "mahadbt.maharashtra.gov.in",
    "agri.maharashtra.gov.in",
    "agri.gov.in",
    "nabard.org",
    "rbi.org.in",
    "myscheme.gov.in",
    "india.gov.in",
    "gov.in",
    "nic.in",
]

# Official portals registry
OFFICIAL_PORTALS: list[dict[str, str]] = [
    {
        "domain": "cooperation.gov.in",
        "title": "Ministry of Cooperation — Official Portal",
        "url": "https://cooperation.gov.in",
        "snippet": "Official portal of the Ministry of Cooperation, Government of India. Formed in July 2021 to provide a dedicated administrative, legal, and policy framework for the cooperative sector.",
    },
    {
        "domain": "pmfby.gov.in",
        "title": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        "url": "https://pmfby.gov.in",
        "snippet": "National Crop Insurance Portal providing insurance enrollment, claim status, crop damage reporting, and seasonal deadlines.",
    },
    {
        "domain": "mahadbt.maharashtra.gov.in",
        "title": "MahaDBT Farmer Schemes — Sub-Mission on Agricultural Mechanization (SMAM)",
        "url": "https://mahadbt.maharashtra.gov.in",
        "snippet": "Maharashtra Direct Benefit Transfer (MahaDBT) Portal for Sub-Mission on Agricultural Mechanization (SMAM) tractor subsidy applications, beneficiary eligibility, and required 7/12 land extract documents.",
    },
    {
        "domain": "agri.gov.in",
        "title": "Sub-Mission on Agricultural Mechanization (SMAM) — Ministry of Agriculture",
        "url": "https://agri.gov.in",
        "snippet": "Official guidelines for Sub-Mission on Agricultural Mechanization (SMAM) providing financial assistance pattern for tractors, power tillers, and agricultural machinery.",
    },
    {
        "domain": "nabard.org",
        "title": "National Bank for Agriculture and Rural Development (NABARD)",
        "url": "https://www.nabard.org",
        "snippet": "Apex development bank for agricultural credit, rural infrastructure funds, and PACS credit refinancing.",
    },
    {
        "domain": "pib.gov.in",
        "title": "Press Information Bureau (PIB) — Cabinet Releases",
        "url": "https://pib.gov.in",
        "snippet": "Official press releases, Union Cabinet decisions, and ministerial notifications from the Ministry of Cooperation and Agriculture.",
    },
]


def get_authority_level(url: str) -> str:
    """Determine the authority level of a given source URL."""
    if not url:
        return "GENERAL"
    url_lower = url.lower()
    if any(domain in url_lower for domain in GOVERNMENT_DOMAINS):
        return "OFFICIAL_GOVERNMENT"
    return "GENERAL"


def search_web_knowledge(query: str, max_results: int = 4) -> List[Dict[str, Any]]:
    """
    Performs trusted live web research.
    Official government sources are prioritized first, followed by general web sources.
    Returns list of dicts with: title, source_url, source_name, snippet, authority_level.
    """
    official_results: List[Dict[str, Any]] = []
    general_results: List[Dict[str, Any]] = []
    clean_query = query.strip()
    query_lower = clean_query.lower()

    # 1. Match Official Portal Registry First (Highest Priority)
    for portal in OFFICIAL_PORTALS:
        dom = portal["domain"]
        if dom == "pmfby.gov.in" and any(w in query_lower for w in ["pmfby", "bima", "insurance", "विमा", "बीमा", "नुकसान", "फसल", "सोयाबीन", "खराब", "ख़राब"]):
            official_results.append({
                "title": portal["title"],
                "source_url": portal["url"],
                "source_name": dom,
                "snippet": portal["snippet"],
                "authority_level": "OFFICIAL_GOVERNMENT",
                "is_trusted": True,
            })
        elif dom in {"mahadbt.maharashtra.gov.in", "agri.gov.in"} and any(w in query_lower for w in ["tractor", "machinery", "smam", "ट्रॅक्टर", "ट्रैक्टर", "अनुदान", "अवजारे", "सबसिडी", "योजना"]):
            official_results.append({
                "title": portal["title"],
                "source_url": portal["url"],
                "source_name": dom,
                "snippet": portal["snippet"],
                "authority_level": "OFFICIAL_GOVERNMENT",
                "is_trusted": True,
            })
        elif dom == "cooperation.gov.in" and any(w in query_lower for w in ["cooperation", "ministry", "minister", "सहकार", "सहकारिता"]):
            official_results.append({
                "title": portal["title"],
                "source_url": portal["url"],
                "source_name": dom,
                "snippet": portal["snippet"],
                "authority_level": "OFFICIAL_GOVERNMENT",
                "is_trusted": True,
            })
        elif dom == "nabard.org" and any(w in query_lower for w in ["nabard", "pacs", "loan", "कर्ज", "ऋण", "नाबार्ड"]):
            official_results.append({
                "title": portal["title"],
                "source_url": portal["url"],
                "source_name": dom,
                "snippet": portal["snippet"],
                "authority_level": "OFFICIAL_GOVERNMENT",
                "is_trusted": True,
            })

    # 2. Live Internet Web Search via DuckDuckGo HTML Parser
    try:
        ddg_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(clean_query)}"
        req = urllib.request.Request(
            ddg_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
        )
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            # Extract URLs, titles, and snippets
            matches = re.findall(
                r'<a class="result__url" href="([^"]+)"[^>]*>\s*(.*?)\s*</a>.*?<a class="result__snippet"[^>]*>(.*?)</a>',
                html,
                re.DOTALL,
            )
            for raw_url, raw_title, raw_snippet in matches[:5]:
                # Extract target URL from DuckDuckGo redirect link
                uddg_match = re.search(r'uddg=([^&]+)', raw_url)
                actual_url = urllib.parse.unquote(uddg_match.group(1)) if uddg_match else raw_url
                if actual_url.startswith("//"):
                    actual_url = "https:" + actual_url

                clean_title = re.sub(r'<[^>]+>', '', raw_title).strip()
                clean_snippet = re.sub(r'<[^>]+>', '', raw_snippet).strip()

                if clean_snippet and len(clean_snippet) > 15:
                    auth = get_authority_level(actual_url)
                    source_name = urllib.parse.urlparse(actual_url).netloc or "web_source"
                    item = {
                        "title": clean_title or f"Live Web Result — {clean_query}",
                        "source_url": actual_url,
                        "source_name": source_name,
                        "snippet": clean_snippet,
                        "authority_level": auth,
                        "is_trusted": True,
                    }
                    if auth == "OFFICIAL_GOVERNMENT":
                        official_results.append(item)
                    else:
                        general_results.append(item)
    except Exception as exc:
        logger.debug("Live DuckDuckGo HTML search exception: %s", exc)

    # 3. Secondary Wikipedia Search (General fallback)
    try:
        wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote_plus(clean_query)}&format=json"
        req = urllib.request.Request(wiki_url, headers={"User-Agent": "SahkaarSetu-AI/1.0"})
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            search_items = data.get("query", {}).get("search", [])
            for item in search_items[:2]:
                title = item.get("title", "")
                snippet = re.sub(r"<[^>]+>", "", item.get("snippet", "")).strip()
                page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title)}"

                if snippet and len(snippet) > 15:
                    general_results.append({
                        "title": f"Wikipedia — {title}",
                        "source_url": page_url,
                        "source_name": "en.wikipedia.org",
                        "snippet": snippet,
                        "authority_level": "GENERAL",
                        "is_trusted": True,
                    })
    except Exception as exc:
        logger.debug("Wikipedia API search error: %s", exc)

    # Combine & Prioritize Official Government Sources First
    all_candidate_results = official_results + general_results

    # Deduplicate results by source_url while preserving authority order
    unique_results = []
    seen = set()
    for r in all_candidate_results:
        url_key = r.get("source_url") or r.get("title")
        if url_key not in seen:
            seen.add(url_key)
            unique_results.append(r)

    final_results = unique_results[:max_results]
    logger.info(f"[WEB RESEARCH] Retrieved {len(final_results)} live internet sources for '{clean_query}' (Official: {len(official_results)})")
    return final_results
