from pydantic import BaseModel
from typing import Optional, List

# --- RAW SCHEMAS (Agent Output) ---

class ArticleSentenceCitation(BaseModel):
    sentence: str
    article_uuid: str
    expert_name: Optional[str] = None

class Citation(BaseModel):
    summary_sentence: str
    article_sentence_citations: List[ArticleSentenceCitation]

class SummaryWithCitations(BaseModel):
    summary_text: str
    citations: List[Citation]


# --- ENRICHED SCHEMAS (App/Frontend Ready) ---

class EnrichedSource(ArticleSentenceCitation):
    """Adds helpfull metadata to the raw citation"""
    article_source: Optional[str] = None
    article_title: Optional[str] = None
    article_url: Optional[str] = None

class EnrichedCitation(BaseModel):
    summary_sentence: str
    sources: List[EnrichedSource]

class EnrichedSummaryWithCitations(BaseModel):
    summary_text: str
    citations: List[EnrichedCitation]
