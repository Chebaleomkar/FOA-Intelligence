"""
NSF Awards API Ingestor.

Uses the NSF Awards API (no authentication required) to search
and fetch National Science Foundation funding/award data.

API Endpoint:
  - GET https://api.nsf.gov/services/v1/awards.json
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
    NSF_AWARDS_URL,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RATE_LIMIT_DELAY,
    SOURCE_NSF,
)

logger = logging.getLogger(__name__)


class NSFIngestor(BaseIngestor):
    """Ingestor for NSF Awards API."""

    # Fields to request from the NSF API
    PRINT_FIELDS = ",".join([
        "id",
        "title",
        "agency",
        "startDate",
        "expDate",
        "abstractText",
        "fundsObligatedAmt",
        "awardeeCity",
        "awardeeStateCode",
        "awardeeName",
        "piFirstName",
        "piLastName",
        "poName",
        "primaryProgram",
        "programElementCode",
        "fundProgramName",
    ])

    @property
    def source_name(self) -> str:
        return SOURCE_NSF

    def _extract_award_id_from_url(self, url: str) -> Optional[str]:
        """
        Extract the award ID from an NSF URL.

        Supports URLs like:
          - https://www.nsf.gov/awardsearch/showAward?AWD_ID=2345678
          - https://nsf.gov/awardsearch/showAward?AWD_ID=2345678&HistoricalAwards=false
        """
        match = re.search(r"AWD_ID=(\d+)", url, re.IGNORECASE)
        if match:
            return match.group(1)

        # Try direct ID pattern
        match = re.search(r"nsf\.gov/.*?/(\d{7})", url)
        if match:
            return match.group(1)

        return None

    def fetch_by_url(self, url: str) -> dict:
        """Fetch a single NSF award by its URL."""
        award_id = self._extract_award_id_from_url(url)

        if award_id:
            return self._fetch_by_id(award_id)

        logger.warning(f"Could not extract award ID from URL: {url}")
        return {"source_url": url, "error": "Could not extract award ID"}

    def _fetch_by_id(self, award_id: str) -> dict:
        """Fetch a single award by its ID."""
        params = {
            "id": award_id,
            "printFields": self.PRINT_FIELDS,
        }

        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(
                    NSF_AWARDS_URL,
                    params=params,
                    timeout=REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                data = response.json()

                awards = data.get("response", {}).get("award", [])
                if awards:
                    logger.info(f"Successfully fetched NSF award {award_id}")
                    return awards[0]
                else:
                    logger.warning(f"No award found with ID {award_id}")
                    return {}

            except requests.RequestException as e:
                logger.warning(
                    f"Attempt {attempt + 1}/{MAX_RETRIES} failed for "
                    f"award {award_id}: {e}"
                )
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RATE_LIMIT_DELAY * (attempt + 1))
                else:
                    raise

    def search(self, keyword: str, max_results: int = 25) -> List[dict]:
        """
        Search NSF awards by keyword.

        Args:
            keyword: Search term.
            max_results: Maximum number of results to return.

        Returns:
            List of award dictionaries.
        """
        results = []
        offset = 1  # NSF API uses 1-based offset
        page_size = min(max_results, 25)

        while len(results) < max_results:
            params = {
                "keyword": keyword,
                "printFields": self.PRINT_FIELDS,
                "offset": offset,
                "rpp": page_size,
            }

            try:
                response = requests.get(
                    NSF_AWARDS_URL,
                    params=params,
                    timeout=REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                data = response.json()

                awards = data.get("response", {}).get("award", [])
                if not awards:
                    break

                results.extend(awards)
                offset += page_size
                time.sleep(RATE_LIMIT_DELAY)

            except requests.RequestException as e:
                logger.error(f"Search failed at offset {offset}: {e}")
                break

        logger.info(f"Found {len(results)} NSF awards for keyword '{keyword}'")
        return results[:max_results]

    def extract_fields(self, raw_data: dict) -> dict:
        """
        Extract standardized fields from NSF API response.

        Maps NSF-specific field names to the unified FOA schema.
        """
        award_id = str(raw_data.get("id", ""))

        # Parse dates (NSF uses MM/DD/YYYY format)
        open_date = self._parse_date(raw_data.get("startDate"))
        close_date = self._parse_date(raw_data.get("expDate"))

        # Award amount
        award_amount = None
        try:
            amt = raw_data.get("fundsObligatedAmt")
            award_amount = float(amt) if amt else None
        except (ValueError, TypeError):
            pass

        # Build source URL
        source_url = (
            f"https://www.nsf.gov/awardsearch/showAward?AWD_ID={award_id}"
            if award_id
            else ""
        )

        # Eligibility info from awardee details
        eligibility_parts = []
        awardee = raw_data.get("awardeeName", "")
        if awardee:
            eligibility_parts.append(f"Awardee: {awardee}")
        pi = f"{raw_data.get('piFirstName', '')} {raw_data.get('piLastName', '')}".strip()
        if pi:
            eligibility_parts.append(f"PI: {pi}")

        # Program description
        description = raw_data.get("abstractText", "")
        program = raw_data.get("primaryProgram") or raw_data.get("fundProgramName", "")
        if program:
            description = f"Program: {program}\n\n{description}"

        return {
            "foa_id": award_id,
            "title": raw_data.get("title", "Unknown"),
            "agency": raw_data.get("agency", "NSF"),
            "open_date": open_date,
            "close_date": close_date,
            "eligibility": "; ".join(eligibility_parts) if eligibility_parts else None,
            "program_description": description if description else None,
            "award_range_min": award_amount,
            "award_range_max": award_amount,
            "source_url": source_url,
            "source": self.source_name,
        }

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse NSF date format (typically MM/DD/YYYY) to ISO date."""
        if not date_str:
            return None
        try:
            dt = date_parser.parse(date_str)
            return dt.date().isoformat()
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not parse NSF date: {date_str} — {e}")
            return None
