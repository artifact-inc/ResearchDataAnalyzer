"""Paper data model."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Paper:
    """Represents a research paper."""

    id: str
    title: str
    abstract: str
    authors: list[str]
    published_date: datetime
    source: str
    url: str
    citation_count: int | None = None
    venue: str | None = None
    full_text: str | None = None
    dataset_mentions: list[str] = field(default_factory=list)
