from pydantic import BaseModel
from typing import Optional, List, Literal

# Fed-specific sentiment type
FedSentiment = Literal["hawkish", "dovish", "neutral"]

# Base citation for LLM prompting - keeps schema clean so agent only fills essential fields
class ArticleSentenceCitationBase(BaseModel):
    """Citation schema for LLM output - agent only needs to provide these fields."""
    sentence: str
    article_uuid: str  # Will be article index from prompt, converted to UUID after
    expert_name: Optional[str] = None


# Enriched citation with metadata - populated by convert_topic_analysis_indexes_to_uuids
class ArticleSentenceCitation(ArticleSentenceCitationBase):
    """Enriched citation with article metadata for display/storage."""
    article_title: Optional[str] = None
    article_source: Optional[str] = None
    article_url: Optional[str] = None


# =============================================================================
# LLM OUTPUT SCHEMAS - Use these as output_schema when prompting the agent
# These use ArticleSentenceCitationBase (no enrichment fields)
# =============================================================================

class CitationLLM(BaseModel):
    """LLM output version - clean schema for agent."""
    summary_sentence: str
    article_sentence_citations: List[ArticleSentenceCitationBase]


class SummaryWithCitationsLLM(BaseModel):
    """LLM output version - clean schema for agent."""
    summary_text: str
    citations: List[CitationLLM]


class EconomicMetricLLM(BaseModel):
    """LLM output version - clean schema for agent."""
    metric_name: str
    value: int
    metric_period: str
    metric_discussion: str 
    sentiment: FedSentiment
    citations: List[ArticleSentenceCitationBase]


class ExpertAnalysisLLM(BaseModel):
    """LLM output version - clean schema for agent."""
    expert_name: str
    expert_organization: str
    expert_opinion: str
    sentiment: FedSentiment
    citations: List[ArticleSentenceCitationBase]


class TopicSummaryAndAnalysisLLM(BaseModel):
    """
    LLM OUTPUT SCHEMA - Use this as output_schema when prompting the agent.
    Clean schema without enrichment fields.
    """
    key_metrics: List[EconomicMetricLLM]
    expert_analyses: List[ExpertAnalysisLLM]
    executive_summary: SummaryWithCitationsLLM
    sentiment: FedSentiment


# =============================================================================
# ENRICHED SCHEMAS - Use these for storage/display after converting indexes
# =============================================================================

class Citation(BaseModel):
    summary_sentence: str
    article_sentence_citations: List[ArticleSentenceCitation]


class SummaryWithCitations(BaseModel):
    summary_text: str
    citations: List[Citation]


class EconomicMetric(BaseModel):
    metric_name: str
    value: float
    metric_period: str
    metric_discussion: str 
    sentiment: FedSentiment
    citations: List[ArticleSentenceCitation]


class ExpertAnalysis(BaseModel):
    expert_name: str
    expert_organization: str
    expert_opinion: str
    sentiment: FedSentiment
    citations: List[ArticleSentenceCitation]


class TopicSummaryAndAnalysis(BaseModel):
    """Enriched version with article metadata for display/storage."""
    key_metrics: List[EconomicMetric]
    expert_analyses: List[ExpertAnalysis]
    executive_summary: SummaryWithCitations
    sentiment: FedSentiment


class TopicAnalysisCollectionLLM(BaseModel):
    """
    LLM OUTPUT SCHEMA for multiple topics.
    Use this when prompting the agent for multiple topic analyses.
    """
    topics: dict[str, TopicSummaryAndAnalysisLLM]


class TopicAnalysisCollection(BaseModel):
    """
    Enriched collection of topic analyses keyed by topic name.
    Use .model_validate_json() to parse from JSON string.
    """
    topics: dict[str, TopicSummaryAndAnalysis]
    
    def __iter__(self):
        return iter(self.topics)
    
    def __getitem__(self, key: str) -> TopicSummaryAndAnalysis:
        return self.topics[key]
    
    def items(self):
        return self.topics.items()
    
    def keys(self):
        return self.topics.keys()
    
    def values(self):
        return self.topics.values()


def convert_topic_analysis_indexes_to_uuids(
    llm_output: dict | TopicAnalysisCollectionLLM,
    article_uuids: List[dict],
) -> TopicAnalysisCollection:
    """
    Convert LLM output with article indices to enriched TopicAnalysisCollection.
    
    Args:
        llm_output: Raw LLM output dict or TopicAnalysisCollectionLLM with article indices
        article_uuids: List of article metadata dicts with 'id', 'source', 'title', 'url'
    
    Returns:
        TopicAnalysisCollection with UUIDs and enriched article details
    """
    def enrich_citation_dict(citation_dict: dict) -> dict:
        """Convert base citation dict to enriched citation dict."""
        idx = citation_dict.get("article_uuid", "")
        if isinstance(idx, str) and idx.isdigit() and int(idx) < len(article_uuids):
            article_meta = article_uuids[int(idx)]
            citation_dict["article_uuid"] = article_meta["id"]
            citation_dict["article_title"] = article_meta.get("title")
            citation_dict["article_source"] = article_meta.get("source")
            citation_dict["article_url"] = article_meta.get("url", "#")
        return citation_dict
    
    # Convert to dict if it's a Pydantic model
    if hasattr(llm_output, "model_dump"):
        data = llm_output.model_dump()
    else:
        data = llm_output
    
    # Get topics dict (handle both {"topics": {...}} and direct dict)
    topics_data = data.get("topics", data)
    
    # Enrich all citations in the data
    for topic_name, topic_analysis in topics_data.items():
        # Process key_metrics citations
        for metric in topic_analysis.get("key_metrics", []):
            metric["citations"] = [
                enrich_citation_dict(c) for c in metric.get("citations", [])
            ]
        
        # Process expert_analyses citations
        for expert in topic_analysis.get("expert_analyses", []):
            expert["citations"] = [
                enrich_citation_dict(c) for c in expert.get("citations", [])
            ]
        
        # Process executive_summary citations
        exec_summary = topic_analysis.get("executive_summary", {})
        for citation in exec_summary.get("citations", []):
            citation["article_sentence_citations"] = [
                enrich_citation_dict(c) for c in citation.get("article_sentence_citations", [])
            ]
    
    # Validate and return enriched collection
    return TopicAnalysisCollection.model_validate({"topics": topics_data})


def print_topic_summary(data: TopicSummaryAndAnalysis | dict, topic_name: str = "Topic Analysis") -> None:
    """
    Pretty print a TopicSummaryAndAnalysis object or dict.
    
    Args:
        data: TopicSummaryAndAnalysis instance or dict with same structure
        topic_name: Optional header name for the analysis
    """
    # Convert dict to model if needed
    if isinstance(data, dict):
        data = TopicSummaryAndAnalysis(**data)
    
    sentiment_emoji = {"hawkish": "🦅", "dovish": "🕊️", "neutral": "⚖️"}
    overall_emoji = sentiment_emoji.get(data.sentiment, "⚪")
    
    print("=" * 80)
    print(f"📊 {topic_name.upper()} {overall_emoji} ({data.sentiment.upper()})")
    print("=" * 80)
    
    # --- KEY METRICS ---
    print(f"\n📈 KEY METRICS ({len(data.key_metrics)} found)")
    print("-" * 40)
    for i, metric in enumerate(data.key_metrics, 1):
        emoji = sentiment_emoji.get(metric.sentiment, "⚪")
        print(f"\n  {i}. {metric.metric_name} {emoji}")
        print(f"     Value: {metric.value:,} | Period: {metric.metric_period}")
        print(f"     Discussion: {metric.metric_discussion}")
        if metric.citations:
            print(f"     📎 Sources: {', '.join(c.article_uuid for c in metric.citations)}")
    
    # --- EXPERT ANALYSES ---
    print(f"\n\n👥 EXPERT ANALYSES ({len(data.expert_analyses)} found)")
    print("-" * 40)
    for i, expert in enumerate(data.expert_analyses, 1):
        emoji = sentiment_emoji.get(expert.sentiment, "⚪")
        print(f"\n  {i}. {expert.expert_name} ({expert.expert_organization}) {emoji}")
        print(f"     Opinion: {expert.expert_opinion}")
        if expert.citations:
            print(f"     📎 Sources: {', '.join(c.article_uuid for c in expert.citations)}")
    
    # --- EXECUTIVE SUMMARY ---
    print("\n\n📝 EXECUTIVE SUMMARY")
    print("-" * 40)
    print(f"\n{data.executive_summary.summary_text}")
    
    if data.executive_summary.citations:
        print(f"\n\n📎 Summary Citations ({len(data.executive_summary.citations)} points):")
        for i, citation in enumerate(data.executive_summary.citations, 1):
            print(f"\n  [{i}] {citation.summary_sentence}")
            for src in citation.article_sentence_citations:
                expert_str = f" ({src.expert_name})" if src.expert_name else ""
                print(f"      └─ Art. {src.article_uuid}{expert_str}: \"{src.sentence[:80]}...\"" 
                      if len(src.sentence) > 80 else f"      └─ Art. {src.article_uuid}{expert_str}: \"{src.sentence}\"")
    
    print("\n" + "=" * 80)