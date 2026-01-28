"""
Pydantic schemas for agent data processing.
These models define the structure of data passed to and from agents.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel


class ArticleMetadata(BaseModel):
    """Metadata for later enrichment (citations, links)."""
    id: str
    source: str
    title: Optional[str] = None
    url: Optional[str] = None


class ArticleContent(BaseModel):
    """Content formatted for LLM consumption."""
    text: Optional[str] = None
    published: Optional[str] = None


class ArticleForAgent(BaseModel):
    """Complete article data - metadata + content in one place."""
    metadata: ArticleMetadata
    content: ArticleContent


class FormattedArticles(BaseModel):
    """Final output: list of articles + helper methods for different formats."""
    articles: List[ArticleForAgent]
    
    def to_llm_dict(self) -> Dict[str, dict]:
        """Convert to indexed dict format for LLM prompts."""
        return {
            str(idx): {
                "source": a.metadata.source,
                "title": a.metadata.title,
                "text": a.content.text,
                "published": a.content.published
            }
            for idx, a in enumerate(self.articles)
        }
    
    def get_metadata_list(self) -> List[dict]:
        """Get just the metadata for enrichment."""
        return [a.metadata.model_dump() for a in self.articles]
    
    def __len__(self) -> int:
        return len(self.articles)
