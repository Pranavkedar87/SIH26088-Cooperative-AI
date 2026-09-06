"""
Trusted Government Web Research Module for SahkaarSetu (SIH26088).

Performs live web research for current, time-sensitive, or scheme update queries.
Prioritizes authoritative government and cooperative domains:
  - *.gov.in, *.nic.in (Government of India portals)
  - pmfby.gov.in (Pradhan Mantri Fasal Bima Yojana)
  - cooperation.gov.in (Ministry of Cooperation)
  - nabard.org (NABARD)
  - rbi.org.in (Reserve Bank of India)
  - maharashtra.gov.in (State Cooperative Dept)
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
TRUSTED_DOMAINS = [
    "gov.in",
    "nic.in",
    "pmfby.gov.in",
    "cooperation.gov.in",
    "nabard.org",
    "rbi.org.in",
    "maharashtra.gov.in",
    "agricoop.nic.in",
    "pib.gov.in",
]


def is_trusted_domain(url: str) -> bool:
    """Check if the given URL belongs to a trusted government or official institutional domain."""
    if not url:
        return False
    url_lower = url.lower()
    return any(domain in url_lower for domain in TRUSTED_DOMAINS)


def search_web_knowledge(query: str, max_results: int = 4) -> List[Dict[str, Any]]:
    """
    Performs trusted live web research using DuckDuckGo HTML / API search endpoint,
    filtering and prioritizing authoritative government sources.
    Returns list of dicts with keys: title, source_url, source_name, snippet.
    """
    results: List[Dict[str, Any]] = []
    clean_query = query.strip()

    # Append site restriction keywords for government prioritization
    gov_search_query = f"{clean_query} site:gov.in OR site:nic.in OR site:nabard.org OR site:rbi.org.in"

    try:
        # Use DuckDuckGo HTML search API
        encoded_query = urllib.parse.quote_plus(gov_search_query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,mr;q=0.8,hi;q=0.7",
        }

        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=6.0) as resp:
            html_text = resp.read().decode("utf-8", errors="ignore")

        # Parse result blocks from DuckDuckGo HTML output
        matches = re.findall(
            r'<a class="result__url" href="([^"]+)".*?<a class="result__snippet[^"]*">(.*?)</a>',
            html_text,
            re.DOTALL,
        )

        for raw_url, raw_snippet in matches[:max_results]:
            # Clean DuckDuckGo redirect URL format (/l/?kh=-1&uddg=http...)
            actual_url = raw_url
            if "uddg=" in raw_url:
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query)
                if "uddg" in parsed:
                    actual_url = parsed["uddg"][0]

            clean_snippet = re.sub(r"<[^>]+>", "", raw_snippet).strip()
            domain_name = urllib.parse.urlparse(actual_url).netloc.replace("www.", "")

            title_match = re.search(r'<a class="result__a"[^>]*>(.*?)</a>', html_text)
            title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip() if title_match else "Official Government Notice"

            results.append({
                "title": title,
                "source_url": actual_url,
                "source_name": domain_name,
                "snippet": clean_snippet,
                "is_trusted": is_trusted_domain(actual_url),
            })

            if len(results) >= max_results:
                break

    except Exception as exc:
        logger.warning(f"[WEB RESEARCH] Primary web search failed: {exc}")

    # Fallback to general search query if site restricted search returned empty
    if not results:
        try:
            encoded_query = urllib.parse.quote_plus(clean_query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            headers = {"User-Agent": "Mozilla/5.0"}
            req = urllib.request.Request(url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                html_text = resp.read().decode("utf-8", errors="ignore")

            matches = re.findall(
                r'<a class="result__url" href="([^"]+)".*?<a class="result__snippet[^"]*">(.*?)</a>',
                html_text,
                re.DOTALL,
            )
            for raw_url, raw_snippet in matches[:max_results]:
                actual_url = raw_url
                if "uddg=" in raw_url:
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query)
                    if "uddg" in parsed:
                        actual_url = parsed["uddg"][0]

                clean_snippet = re.sub(r"<[^>]+>", "", raw_snippet).strip()
                domain_name = urllib.parse.urlparse(actual_url).netloc.replace("www.", "")

                results.append({
                    "title": "Government & Cooperative Resource",
                    "source_url": actual_url,
                    "source_name": domain_name,
                    "snippet": clean_snippet,
                    "is_trusted": is_trusted_domain(actual_url),
                })
                if len(results) >= max_results:
                    break
        except Exception as exc:
            logger.warning(f"[WEB RESEARCH] Fallback web search failed: {exc}")

    logger.info(f"[WEB RESEARCH] Retrieved {len(results)} live web search results for query '{clean_query}'")
    return results
