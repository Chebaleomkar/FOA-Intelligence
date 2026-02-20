"""
Ontology Loader — Loads and manages the controlled vocabulary.

Reads the ontology.yaml file and provides methods to access
tags, synonyms, and hierarchical relationships.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from config.settings import ONTOLOGY_PATH

logger = logging.getLogger(__name__)


class OntologyTag:
    """Represents a single tag in the ontology."""

    def __init__(self, category: str, name: str, synonyms: List[str] = None, children: List[str] = None):
        self.category = category          # e.g., "research_domains"
        self.name = name                  # e.g., "artificial_intelligence"
        self.synonyms = synonyms or []    # e.g., ["AI", "machine learning"]
        self.children = children or []    # e.g., ["nlp", "computer_vision"]

    @property
    def full_path(self) -> str:
        """Returns category/name path (e.g., 'research_domains/artificial_intelligence')."""
        return f"{self.category}/{self.name}"

    @property
    def all_terms(self) -> List[str]:
        """Returns name + all synonyms for matching."""
        terms = [self.name.replace("_", " ")]
        terms.extend(self.synonyms)
        return terms

    def __repr__(self):
        return f"OntologyTag({self.full_path})"


class Ontology:
    """Loads and provides access to the controlled vocabulary."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or ONTOLOGY_PATH
        self.tags: List[OntologyTag] = []
        self.categories: Dict[str, List[OntologyTag]] = {}
        self._load()

    def _load(self):
        """Load ontology from YAML file."""
        logger.info(f"Loading ontology from {self.path}")

        with open(self.path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for category, tag_list in data.items():
            self.categories[category] = []

            for tag_entry in tag_list:
                if isinstance(tag_entry, dict):
                    name = tag_entry.get("name", "")
                    synonyms = tag_entry.get("synonyms", [])
                    children = tag_entry.get("children", [])
                elif isinstance(tag_entry, str):
                    name = tag_entry
                    synonyms = []
                    children = []
                else:
                    continue

                tag = OntologyTag(
                    category=category,
                    name=name,
                    synonyms=synonyms,
                    children=children,
                )
                self.tags.append(tag)
                self.categories[category].append(tag)

        logger.info(
            f"Loaded {len(self.tags)} tags across "
            f"{len(self.categories)} categories"
        )

    def get_tags_by_category(self, category: str) -> List[OntologyTag]:
        """Get all tags in a specific category."""
        return self.categories.get(category, [])

    def get_all_tags(self) -> List[OntologyTag]:
        """Get all tags across all categories."""
        return self.tags

    def get_tag_by_name(self, name: str) -> Optional[OntologyTag]:
        """Find a tag by name (case-insensitive)."""
        name_lower = name.lower()
        for tag in self.tags:
            if tag.name.lower() == name_lower:
                return tag
        return None
