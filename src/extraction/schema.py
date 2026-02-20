"""
FOA Schema — Pydantic models for Funding Opportunity Announcements.

Defines the standardized schema that all FOA records must conform to,
regardless of their source (Grants.gov, NSF, etc.).
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
import uuid


class SemanticTag(BaseModel):
    """A semantic tag applied to an FOA."""
    tag: str                          # e.g., "research_domains/artificial_intelligence"
    confidence: float = Field(ge=0.0, le=1.0)
    method: str                       # "rule_based" | "embedding" | "llm"


class FOARecord(BaseModel):
    """
    Standardized Funding Opportunity Announcement record.

    All FOAs from any source are normalized into this schema
    before export to JSON/CSV.
    """
    foa_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique ID for the FOA. Uses the source's ID if available, otherwise UUID."
    )
    title: str = Field(
        description="Title of the funding opportunity."
    )
    agency: str = Field(
        description="Funding agency (e.g., 'NSF', 'DOE', 'NIH')."
    )
    open_date: Optional[date] = Field(
        default=None,
        description="Date the opportunity opens for applications (ISO format)."
    )
    close_date: Optional[date] = Field(
        default=None,
        description="Application deadline (ISO format)."
    )
    eligibility: Optional[str] = Field(
        default=None,
        description="Eligibility requirements text."
    )
    program_description: Optional[str] = Field(
        default=None,
        description="Description of the funding program/opportunity."
    )
    award_range_min: Optional[float] = Field(
        default=None,
        description="Minimum award amount in USD."
    )
    award_range_max: Optional[float] = Field(
        default=None,
        description="Maximum award amount in USD."
    )
    source_url: str = Field(
        description="URL of the source where this FOA was found."
    )
    source: str = Field(
        description="Source identifier: 'grants_gov' or 'nsf'."
    )
    semantic_tags: List[SemanticTag] = Field(
        default_factory=list,
        description="Semantic tags applied to this FOA."
    )
    ingested_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when this FOA was ingested."
    )

    def to_flat_dict(self) -> dict:
        """
        Convert to a flat dictionary suitable for CSV export.
        Semantic tags are joined as a semicolon-separated string.
        """
        data = self.model_dump()
        # Flatten dates to ISO strings
        data["open_date"] = self.open_date.isoformat() if self.open_date else ""
        data["close_date"] = self.close_date.isoformat() if self.close_date else ""
        data["ingested_at"] = self.ingested_at.isoformat()
        # Flatten semantic tags
        data["semantic_tags"] = "; ".join(
            f"{t.tag} ({t.confidence:.2f}, {t.method})"
            for t in self.semantic_tags
        )
        return data
