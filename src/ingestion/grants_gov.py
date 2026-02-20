"""
Grants.gov API Ingestor.

Uses the public Grants.gov REST API (no authentication required) to
search and fetch Funding Opportunity Announcements.

API Endpoints:
  - POST https://api.grants.gov/v1/api/search2
  - POST https://api.grants.gov/v1/api/fetchOpportunity
"""

import re
import time
import logging
from typing import List, Optional
from datetime import datetime
from dateutil import parser as date_parser

import requests

from src.ingestion.base import BaseIngestor
from config.settings import (
    GRANTS_GOV_SEARCH_URL,
    GRANTS_GOV_FETCH_URL,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RATE_LIMIT_DELAY,
    SOURCE_GRANTS_GOV,
)

logger = logging.getLogger(__name__)


class GrantsGovIngestor(BaseIngestor):
    """Ingestor for Grants.gov public API."""

    @property
    def source_name(self) -> str:
        return SOURCE_GRANTS_GOV

    def _extract_opportunity_id_from_url(self, url: str) -> Optional[int]:
        """
        Extract the opportunity ID from a Grants.gov URL.

        Supports URLs like:
          - https://www.grants.gov/search-results-detail/123456
          - https://grants.gov/search-results-detail/123456
        """
        patterns = [
            r"grants\.gov/search-results-detail/(\d+)",
            r"grants\.gov/view-opportunity/html/\?oppId=(\d+)",
            r"grants\.gov.*[?&]oppId=(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return int(match.group(1))
        return None

    def fetch_by_url(self, url: str) -> dict:
        """
        Fetch a single FOA from Grants.gov by URL.

        Tries to extract the opportunity ID from the URL and
        use the API. Falls back to basic metadata if ID not found.
        """
        opp_id = self._extract_opportunity_id_from_url(url)

        if opp_id:
            return self._fetch_by_id(opp_id)

        # If we can't extract an ID, try to search by URL components
        logger.warning(
            f"Could not extract opportunity ID from URL: {url}. "
            "Attempting keyword search fallback."
        )
        return {"source_url": url, "error": "Could not extract opportunity ID"}

    def _fetch_by_id(self, opp_id: int) -> dict:
        """
        Fetch detailed opportunity data by numeric ID.
        
        Tries fetchOpportunity first, falls back to search2 if it fails.
        """
        # Try fetchOpportunity endpoint first
        payload = {"oppId": opp_id}

        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    GRANTS_GOV_FETCH_URL,
                    json=payload,
                    timeout=REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                data = response.json()
                
                # Unwrap 'data' key if present
                inner = data.get("data", data)
                
                # Check if the backend actually returned useful data
                if inner.get("opportunity") or inner.get("title"):
                    logger.info(f"Successfully fetched Grants.gov opportunity {opp_id} via fetchOpportunity")
                    return inner
                
                # If fetchOpportunity returned no data, fall through to search fallback
                if inner.get("message") or not inner.get("opportunity"):
                    logger.warning(f"fetchOpportunity returned no data for {opp_id}, trying search fallback")
                    break
                    
            except requests.RequestException as e:
                logger.warning(
                    f"Attempt {attempt + 1}/{MAX_RETRIES} failed for "
                    f"opportunity {opp_id}: {e}"
                )
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RATE_LIMIT_DELAY * (attempt + 1))
                else:
                    break  # Fall through to search fallback
        
        # Fallback: Use search2 to find the opportunity by ID
        return self._search_by_id_fallback(opp_id)
    
    def _search_by_id_fallback(self, opp_id: int) -> dict:
        """
        Fallback: search for an opportunity by its ID when fetchOpportunity is unavailable.
        """
        logger.info(f"Using search2 fallback for opportunity {opp_id}")
        
        try:
            payload = {
                "keyword": str(opp_id),
                "oppStatuses": "forecasted|posted|closed|archived",
                "rows": 5,
                "offset": 0,
            }
            response = requests.post(
                GRANTS_GOV_SEARCH_URL,
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            inner = data.get("data", data)
            hits = inner.get("oppHits", [])
            
            # Find the exact match by ID
            for hit in hits:
                if str(hit.get("id")) == str(opp_id):
                    logger.info(f"Found opportunity {opp_id} via search fallback")
                    return hit
            
            # If exact match not found, return first result
            if hits:
                logger.warning(f"Exact ID match not found, returning best match for {opp_id}")
                return hits[0]
            
        except requests.RequestException as e:
            logger.error(f"Search fallback also failed for {opp_id}: {e}")
        
        return {"error": f"Could not fetch opportunity {opp_id}"}

    def search(self, keyword: str, max_results: int = 25) -> List[dict]:
        """
        Search Grants.gov for funding opportunities by keyword.

        Args:
            keyword: Search term (e.g., 'artificial intelligence', 'climate').
            max_results: Maximum number of results to fetch.

        Returns:
            List of opportunity dictionaries.
        """
        results = []
        offset = 0
        page_size = min(max_results, 25)

        while len(results) < max_results:
            payload = {
                "keyword": keyword,
                "oppStatuses": "forecasted|posted",
                "sortBy": "openDate|desc",
                "rows": page_size,
                "offset": offset,
            }

            try:
                response = requests.post(
                    GRANTS_GOV_SEARCH_URL,
                    json=payload,
                    timeout=REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                data = response.json()

                # Results are nested under "data" key
                inner = data.get("data", data)
                opportunities = inner.get("oppHits", [])
                if not opportunities:
                    break

                results.extend(opportunities)
                offset += page_size
                time.sleep(RATE_LIMIT_DELAY)

            except requests.RequestException as e:
                logger.error(f"Search failed at offset {offset}: {e}")
                break

        logger.info(f"Found {len(results)} opportunities for keyword '{keyword}'")
        return results[:max_results]

    def extract_fields(self, raw_data: dict) -> dict:
        """
        Extract standardized fields from Grants.gov API response.

        Maps Grants.gov-specific field names to the unified FOA schema.
        """
        # The API response structure varies between search2 and fetchOpportunity
        # Handle both formats
        opportunity = raw_data.get("opportunity", raw_data)
        synopsis = raw_data.get("synopsis", {})

        # Merge opportunity and synopsis data
        if synopsis:
            opportunity = {**opportunity, **synopsis}

        # Extract opportunity number or ID
        # search2 uses "number" and "id"; fetchOpportunity uses "opportunityNumber"/"oppId"
        foa_id = (
            str(opportunity.get("number", ""))
            or str(opportunity.get("opportunityNumber", ""))
            or str(opportunity.get("oppId", ""))
            or str(opportunity.get("id", ""))
        )

        # Parse dates
        open_date = self._parse_date(
            opportunity.get("openDate")
            or opportunity.get("postDate")
            or opportunity.get("postingDate")
        )
        close_date = self._parse_date(
            opportunity.get("closeDate")
            or opportunity.get("responseDate")
            or opportunity.get("archiveDate")
        )

        # Extract award amounts
        award_floor, award_ceiling = self._extract_award_range(opportunity)

        # Build source URL
        opp_id = opportunity.get("oppId") or opportunity.get("id")
        source_url = (
            f"https://www.grants.gov/search-results-detail/{opp_id}"
            if opp_id
            else ""
        )

        # Combine description fields
        description_parts = []
        for field in ["synopsis", "synopsisDesc", "description", "opportunityTitle"]:
            val = opportunity.get(field)
            if val and isinstance(val, str) and len(val) > 20:
                description_parts.append(val)

        return {
            "foa_id": foa_id,
            "title": opportunity.get("title", opportunity.get("opportunityTitle", "Unknown")),
            "agency": opportunity.get("agency", opportunity.get("agencyName", "Unknown")),
            "open_date": open_date,
            "close_date": close_date,
            "eligibility": opportunity.get("eligibility", None),
            "program_description": "\n\n".join(description_parts) if description_parts else None,
            "award_range_min": award_floor,
            "award_range_max": award_ceiling,
            "source_url": source_url,
            "source": self.source_name,
        }

    def _parse_date(self, date_value) -> Optional[str]:
        """Parse various date formats to ISO date string."""
        if not date_value:
            return None
        try:
            # Handle Unix timestamp (milliseconds)
            if isinstance(date_value, (int, float)):
                dt = datetime.fromtimestamp(date_value / 1000)
                return dt.date().isoformat()
            # Handle string dates
            if isinstance(date_value, str):
                dt = date_parser.parse(date_value)
                return dt.date().isoformat()
        except (ValueError, TypeError, OverflowError) as e:
            logger.warning(f"Could not parse date: {date_value} — {e}")
        return None

    def _extract_award_range(self, data: dict) -> tuple:
        """Extract award floor and ceiling amounts."""
        award_floor = data.get("awardFloor") or data.get("fundingFloor")
        award_ceiling = data.get("awardCeiling") or data.get("fundingCeiling")

        try:
            award_floor = float(award_floor) if award_floor else None
        except (ValueError, TypeError):
            award_floor = None

        try:
            award_ceiling = float(award_ceiling) if award_ceiling else None
        except (ValueError, TypeError):
            award_ceiling = None

        return award_floor, award_ceiling
