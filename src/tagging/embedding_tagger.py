"""
Embedding-Based Tagger — Semantic similarity using sentence-transformers.

Computes cosine similarity between FOA text embeddings and
pre-computed ontology tag embeddings to assign semantic tags.
"""

import logging
from typing import List, Optional

import numpy as np

from src.extraction.schema import SemanticTag
from src.tagging.ontology import Ontology
from config.settings import EMBEDDING_MODEL, EMBEDDING_SIMILARITY_THRESHOLD

logger = logging.getLogger(__name__)


class EmbeddingTagger:
    """
    Tags FOA text using semantic similarity with sentence-transformers.

    On initialization, pre-computes embeddings for all ontology terms.
    At tag time, encodes the FOA text and finds nearest ontology tags.
    """

    def __init__(
        self,
        ontology: Optional[Ontology] = None,
        model_name: str = EMBEDDING_MODEL,
        threshold: float = EMBEDDING_SIMILARITY_THRESHOLD,
    ):
        self.ontology = ontology or Ontology()
        self.model_name = model_name
        self.threshold = threshold
        self.model = None
        self.reference_embeddings = None
        self.tag_paths: List[str] = []
        self._initialized = False

    def _lazy_init(self):
        """
        Lazily initialize the model and reference embeddings.
        This avoids expensive model loading until actually needed.
        """
        if self._initialized:
            return

        try:
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity

            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self._cosine_similarity = cosine_similarity
            self._build_reference_embeddings()
            self._initialized = True
            logger.info(
                f"Embedding tagger ready with {len(self.tag_paths)} reference tags"
            )

        except ImportError as e:
            logger.error(
                f"sentence-transformers or scikit-learn not installed: {e}. "
                "Embedding tagger will not be available."
            )
            raise

    def _build_reference_embeddings(self):
        """Pre-compute embeddings for all ontology tag descriptions."""
        tag_texts = []
        self.tag_paths = []

        for tag in self.ontology.get_all_tags():
            # Create a representative text for each tag
            terms = tag.all_terms
            text = " ".join(terms)
            tag_texts.append(text)
            self.tag_paths.append(tag.full_path)

        self.reference_embeddings = self.model.encode(
            tag_texts,
            show_progress_bar=False,
            normalize_embeddings=True,
        )

        logger.info(f"Built {len(tag_texts)} reference embeddings")

    def tag(self, title: str, description: str = "") -> List[SemanticTag]:
        """
        Apply embedding-based semantic tags to FOA text.

        Args:
            title: FOA title.
            description: FOA description/abstract.

        Returns:
            List of SemanticTag objects sorted by confidence.
        """
        self._lazy_init()

        combined_text = f"{title}. {description}" if description else title

        # Encode the query text
        query_embedding = self.model.encode(
            [combined_text],
            show_progress_bar=False,
            normalize_embeddings=True,
        )

        # Compute cosine similarity with all reference tags
        similarities = self._cosine_similarity(
            query_embedding, self.reference_embeddings
        )[0]

        # Filter by threshold and create SemanticTag objects
        tags = []
        for i, sim in enumerate(similarities):
            if sim >= self.threshold:
                tags.append(
                    SemanticTag(
                        tag=self.tag_paths[i],
                        confidence=float(round(sim, 4)),
                        method="embedding",
                    )
                )

        # Sort by confidence descending
        tags.sort(key=lambda t: t.confidence, reverse=True)

        logger.debug(
            f"Embedding tagger found {len(tags)} tags "
            f"(threshold={self.threshold}) for: {title[:60]}"
        )
        return tags
