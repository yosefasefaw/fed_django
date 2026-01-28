from typing import List
from django.db import transaction
from .models import Summary, Citation, CitationSource
from news.models import Article
from .dn_mas.schemas import EnrichedSummaryWithCitations

def save_dn_mas_summary(
    enriched_summary: EnrichedSummaryWithCitations, 
    articles_list: List[Article], 
    start_date=None, 
    end_date=None, 
    agent_name: str = "dn_mas"
) -> Summary:
    """
    Saves a DN-MAS summary and its citations to the database.
    Uses a transaction to ensure atomicity.
    """
    with transaction.atomic():
        # 1. Create the parent Summary object
        summary_obj = Summary.objects.create(
            summary_text=enriched_summary.summary_text,
            article_count=len(articles_list),
            date_range_start=start_date,
            date_range_end=end_date,
            agent_name=agent_name
        )
        
        # 2. Link all Articles provided to the agent
        summary_obj.articles_provided.set(articles_list)
        
        # 3. Create Citations and their Sources
        for i, citation_data in enumerate(enriched_summary.citations):
            citation_obj = Citation.objects.create(
                summary=summary_obj,
                summary_sentence=citation_data.summary_sentence,
                order=i
            )
            
            for source_data in citation_data.sources:
                # Try to find the actual Article object using the UUID
                article_obj = Article.objects.filter(uuid=source_data.article_uuid).first()
                
                CitationSource.objects.create(
                    citation=citation_obj,
                    article=article_obj,
                    sentence=source_data.sentence,
                    expert_name=source_data.expert_name,
                    article_uuid=source_data.article_uuid,
                    article_source=source_data.article_source,
                    article_title=source_data.article_title,
                    article_url=source_data.article_url
                )
                
    return summary_obj
