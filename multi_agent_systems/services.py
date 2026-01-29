from typing import List
from django.db import transaction
from .models import (
    Summary,
    Citation,
    CitationSource,
    TopicAnalysisGroup,
    TopicAnalysis,
    TopicMetric,
    TopicExpert,
    TopicCitation,
    TopicCitationSource,
)
from news.models import Article
from .dn_mas.schemas import EnrichedSummaryWithCitations
from .st_mas.schemas import TopicAnalysisCollection


def save_dn_mas_summary(
    enriched_summary: EnrichedSummaryWithCitations,
    articles_list: List[Article],
    start_date=None,
    end_date=None,
    agent_name: str = "dn_mas",
    context: str = "general",
    fomc_announcement_datetime=None,
) -> Summary:
    """
    Saves a DN-MAS summary and its citations to the database.
    Uses a transaction to ensure atomicity.
    """
    if fomc_announcement_datetime and isinstance(fomc_announcement_datetime, str):
        from django.utils.dateparse import parse_datetime
        from django.utils import timezone
        fomc_announcement_datetime = parse_datetime(fomc_announcement_datetime)
        if fomc_announcement_datetime and timezone.is_naive(fomc_announcement_datetime):
            fomc_announcement_datetime = timezone.make_aware(fomc_announcement_datetime)
    elif fomc_announcement_datetime and hasattr(fomc_announcement_datetime, 'hour'):
        from django.utils import timezone
        if timezone.is_naive(fomc_announcement_datetime):
            fomc_announcement_datetime = timezone.make_aware(fomc_announcement_datetime)

    with transaction.atomic():
        # 1. Create the parent Summary object
        summary_obj = Summary.objects.create(
            summary_text=enriched_summary.summary_text,
            article_count=len(articles_list),
            date_range_start=start_date,
            date_range_end=end_date,
            agent_name=agent_name,
            context=context,
            fomc_announcement_datetime=fomc_announcement_datetime,
        )

        # 2. Link all Articles provided to the agent
        summary_obj.articles_provided.set(articles_list)

        # 3. Create Citations and their Sources
        for i, citation_data in enumerate(enriched_summary.citations):
            citation_obj = Citation.objects.create(
                summary=summary_obj,
                summary_sentence=citation_data.summary_sentence,
                order=i,
            )

            for source_data in citation_data.sources:
                # Try to find the actual Article object using the UUID
                article_obj = Article.objects.filter(
                    uuid=source_data.article_uuid
                ).first()

                CitationSource.objects.create(
                    citation=citation_obj,
                    article=article_obj,
                    sentence=source_data.sentence,
                    expert_name=source_data.expert_name,
                    article_uuid=source_data.article_uuid,
                    article_source=source_data.article_source,
                    article_title=source_data.article_title,
                    article_url=source_data.article_url,
                )

    return summary_obj


def save_st_mas_collection(
    collection: TopicAnalysisCollection,
    articles_list: List[Article],
    agent_name: str = "st_mas",
    context: str = "general",
    fomc_announcement_datetime=None,
) -> TopicAnalysisGroup:
    """
    Saves a collection of topic analyses (ST-MAS) to the database.
    """
    if fomc_announcement_datetime and isinstance(fomc_announcement_datetime, str):
        from django.utils.dateparse import parse_datetime
        from django.utils import timezone
        fomc_announcement_datetime = parse_datetime(fomc_announcement_datetime)
        if fomc_announcement_datetime and timezone.is_naive(fomc_announcement_datetime):
            fomc_announcement_datetime = timezone.make_aware(fomc_announcement_datetime)
    elif fomc_announcement_datetime and hasattr(fomc_announcement_datetime, 'hour'):
        from django.utils import timezone
        if timezone.is_naive(fomc_announcement_datetime):
            fomc_announcement_datetime = timezone.make_aware(fomc_announcement_datetime)

    with transaction.atomic():
        # 1. Create the Group
        group_obj = TopicAnalysisGroup.objects.create(
            agent_name=agent_name,
            context=context,
            fomc_announcement_datetime=fomc_announcement_datetime,
        )
        group_obj.articles_provided.set(articles_list)

        # 2. Process each Topic
        for topic_name, analysis in collection.items():
            topic_obj = TopicAnalysis.objects.create(
                group=group_obj,
                topic_name=topic_name,
                sentiment=analysis.sentiment,
                summary_text=analysis.executive_summary.summary_text,
            )

            # 3. Save Metrics
            for metric in analysis.key_metrics:
                metric_obj = TopicMetric.objects.create(
                    topic_analysis=topic_obj,
                    name=metric.metric_name,
                    value=str(metric.value),
                    period=metric.metric_period,
                    discussion=metric.metric_discussion,
                    sentiment=metric.sentiment,
                )
                # Metric Citations
                _save_topic_citations(metric_obj, metric.citations, "metric")

            # 4. Save Experts
            for expert in analysis.expert_analyses:
                expert_obj = TopicExpert.objects.create(
                    topic_analysis=topic_obj,
                    expert_name=expert.expert_name,
                    organization=expert.expert_organization,
                    opinion=expert.expert_opinion,
                    sentiment=expert.sentiment,
                )
                # Expert Citations
                _save_topic_citations(expert_obj, expert.citations, "expert")

            # 5. Save Summary Citations
            _save_topic_citations(
                topic_obj, analysis.executive_summary.citations, "analysis"
            )

    return group_obj


def _save_topic_citations(parent_obj, citations_data, parent_type: str):
    """Internal helper to save ST-MAS citations."""
    for i, citation in enumerate(citations_data):
        # Handle the different structure of executive summary citations vs metric/expert citations
        # Metrics/Experts have a direct list of ArticleSentenceCitation
        # Executive summary has a list of Citations which contain article_sentence_citations

        if parent_type == "analysis":
            # For the executive summary
            summary_sentence = citation.summary_sentence
            sources = citation.article_sentence_citations
        else:
            # For metrics and experts, there is no 'summary_sentence' per citation item in the schema
            # they are just a list of backing sources.
            summary_sentence = f"Source for {parent_obj}"
            sources = [citation] if not isinstance(citation, list) else citation

        topic_citation = TopicCitation.objects.create(
            summary_sentence=summary_sentence, order=i
        )

        if parent_type == "analysis":
            topic_citation.topic_analysis = parent_obj
        elif parent_type == "metric":
            topic_citation.metric = parent_obj
        elif parent_type == "expert":
            topic_citation.expert = parent_obj

        topic_citation.save()

        # Save sources
        for src in sources:
            article_obj = Article.objects.filter(uuid=src.article_uuid).first()
            TopicCitationSource.objects.create(
                topic_citation=topic_citation,
                article=article_obj,
                sentence=src.sentence,
                expert_name=src.expert_name,
                article_uuid=src.article_uuid,
                article_source=src.article_source,
                article_title=src.article_title,
                article_url=src.article_url,
            )
