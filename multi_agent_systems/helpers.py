"""
Shared helper functions for all agents.
These functions prepare and format data for agent consumption.
"""

from typing import Dict, List
from django.db.models import QuerySet

from .schemas import ArticleMetadata, ArticleContent, ArticleForAgent, FormattedArticles
from multi_agent_systems.dn_mas.schemas import (
    SummaryWithCitations,
    Citation as CitationSchema,
    ArticleSentenceCitation,
    EnrichedSummaryWithCitations,
    EnrichedCitation,
    EnrichedSource,
)


def format_articles_for_agent(articles_qs: QuerySet) -> FormattedArticles:
    """
    Converts a queryset of Articles into a Pydantic model suitable for agent processing.
    """
    articles = []
    metadata_list = []

    for article in articles_qs:
        meta = ArticleMetadata(
            id=str(article.uuid),
            source=str(article.source) if article.source else "Unknown",
            title=article.title,
            url=article.url,
        )
        content = ArticleContent(text=article.body or "")
        articles.append(ArticleForAgent(metadata=meta, content=content))
        metadata_list.append(meta.model_dump())

    return FormattedArticles(articles=articles, metadata_list=metadata_list)


def create_idx_to_metadata_map(metadata_list: List[dict]) -> Dict[str, dict]:
    """
    Creates a mapping from article index (as string) to its full metadata.
    """
    return {str(i): meta for i, meta in enumerate(metadata_list)}


def enrich_summary_to_app_model(
    summary: SummaryWithCitations, idx_to_metadata: Dict[str, dict]
) -> EnrichedSummaryWithCitations:
    """
    Converts raw agent output into a fully enriched 'App-Ready' Pydantic model.
    Replaces indices with real UUIDs and adds Source, Title, and URL.
    """
    enriched_citations = []

    for citation in summary.citations:
        sources = []
        for source in citation.article_sentence_citations:
            # Look up metadata using the agent's index (fallback to idx if not found)
            meta = idx_to_metadata.get(source.article_uuid, {})

            sources.append(
                EnrichedSource(
                    sentence=source.sentence,
                    article_uuid=meta.get("id", source.article_uuid),
                    expert_name=source.expert_name,
                    article_source=meta.get("source", "Unknown"),
                    article_title=meta.get("title"),
                    article_url=meta.get("url"),
                )
            )

        enriched_citations.append(
            EnrichedCitation(
                summary_sentence=citation.summary_sentence, sources=sources
            )
        )

    return EnrichedSummaryWithCitations(
        summary_text=summary.summary_text, citations=enriched_citations
    )
