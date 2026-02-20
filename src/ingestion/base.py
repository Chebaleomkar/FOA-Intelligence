"""
Abstract base class for FOA ingestion sources.

All source connectors (Grants.gov, NSF, etc.) must implement
this interface for consistent pipeline behavior.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class BaseIngestor(ABC):
    """Abstract base class for FOA data sources."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the name of the data source (e.g., 'grants_gov', 'nsf')."""
        ...

    @abstractmethod
    def fetch_by_url(self, url: str) -> dict:
        """
        Fetch a single FOA by its URL.

        Args:
            url: The URL of the funding opportunity.

        Returns:
            Raw data dictionary from the source.
        """
        ...

    @abstractmethod
    def search(self, keyword: str, max_results: int = 25) -> List[dict]:
        """
        Search for FOAs by keyword.

        Args:
            keyword: Search term.
            max_results: Maximum number of results to return.

        Returns:
            List of raw data dictionaries from the source.
        """
        ...

    @abstractmethod
    def extract_fields(self, raw_data: dict) -> dict:
        """
        Extract standardized fields from raw source data.

        Args:
            raw_data: Raw data from the source API/scrape.

        Returns:
            Dictionary with fields matching FOARecord schema.
        """
        ...
