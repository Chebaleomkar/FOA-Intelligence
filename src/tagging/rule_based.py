"""
Rule-Based Tagger — Keyword and regex matching.

Applies deterministic tags to FOA text based on
keyword matches against the controlled ontology.
"""

import re
import logging
from typing import List, Optional

from src.extraction.schema import SemanticTag
from src.tagging.ontology import Ontology, OntologyTag

logger = logging.getLogger(__name__)


class RuleBasedTagger:
    """
    Tags FOA text using keyword matching against the ontology.

    Scoring logic:
      - Each term match adds to a raw score
      - Score is normalized by the number of terms checked
      - Title matches get a 2x weight boost
      - Final confidence is clamped to [0, 1]
    """

    TITLE_WEIGHT = 2.0
    MIN_CONFIDENCE = 0.15  # Minimum score to consider a tag

    def __init__(self, ontology: Optional[Ontology] = None):
        self.ontology = ontology or Ontology()
        logger.info(
            f"RuleBasedTagger initialized with {len(self.ontology.tags)} tags"
        )

    def tag(self, title: str, description: str = "") -> List[SemanticTag]:
        """
        Apply rule-based semantic tags to FOA text.

        Args:
            title: FOA title text.
            description: FOA description/abstract text.

        Returns:
            List of SemanticTag objects with confidence scores.
        """
        tags = []
        combined_text = f"{title} {description}".lower()
        title_lower = title.lower()

        for ontology_tag in self.ontology.get_all_tags():
            confidence = self._compute_confidence(
                ontology_tag, title_lower, combined_text
            )

            if confidence >= self.MIN_CONFIDENCE:
                tags.append(
                    SemanticTag(
                        tag=ontology_tag.full_path,
                        confidence=min(confidence, 1.0),
                        method="rule_based",
                    )
                )

        # Sort by confidence descending
        tags.sort(key=lambda t: t.confidence, reverse=True)

        logger.debug(f"Rule-based tagger found {len(tags)} tags for: {title[:60]}")
        return tags

    def _compute_confidence(
        self,
        ontology_tag: OntologyTag,
        title_lower: str,
        combined_text: str,
    ) -> float:
        """
        Compute confidence score for a tag against the text.

        Uses term frequency with title boost.
        """
        terms = ontology_tag.all_terms
        if not terms:
            return 0.0

        total_score = 0.0

        for term in terms:
            term_lower = term.lower()

            # Check title match (higher weight)
            if self._term_in_text(term_lower, title_lower):
                total_score += self.TITLE_WEIGHT

            # Check description match
            if self._term_in_text(term_lower, combined_text):
                total_score += 1.0

        # Normalize: score / (max possible score per term * num terms)
        max_possible = (self.TITLE_WEIGHT + 1.0) * len(terms)
        confidence = total_score / max_possible if max_possible > 0 else 0.0

        return confidence

    def _term_in_text(self, term: str, text: str) -> bool:
        """
        Check if a term appears in text as a whole word/phrase.

        Uses word boundary matching to avoid partial matches
        (e.g., 'AI' should not match 'training').
        """
        # For single-character or very short terms, require word boundaries
        if len(term) <= 3:
            pattern = rf"\b{re.escape(term)}\b"
            return bool(re.search(pattern, text, re.IGNORECASE))
        else:
            return term in text
