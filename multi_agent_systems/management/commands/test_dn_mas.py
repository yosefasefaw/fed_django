"""
Management command to test the DN-MAS (Dynamic News Multi-Agent System) pipeline.
"""

import asyncio
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from news.selectors import get_articles_from_db
from multi_agent_systems.helpers import (
    format_articles_for_agent,
    create_idx_to_metadata_map,
    enrich_summary_to_app_model,
)
from multi_agent_systems.dn_mas.runner import dn_mas_runner
from multi_agent_systems.dn_mas.schemas import SummaryWithCitations
from multi_agent_systems.services import save_dn_mas_summary


class Command(BaseCommand):
    help = "Test the DN-MAS agent pipeline with articles from the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Number of days to look back for articles (default: 7)",
        )
        parser.add_argument(
            "--filter-sources",
            action="store_true",
            help="Only use trusted sources from SOURCE_TITLES",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=5,
            help="Maximum number of articles to process (default: 5)",
        )
        parser.add_argument(
            "--save",
            action="store_true",
            help="Save the summary and citations to the database",
        )
        parser.add_argument(
            "--context",
            type=str,
            default="general",
            help="Context for the analysis (pre_announcement, post_announcement, general)",
        )
        parser.add_argument(
            "--fomc-time",
            "--fomc",
            type=str,
            default=None,
            help="FOMC announcement datetime (e.g., '2025-12-18 14:00')",
        )

    def handle(self, *args, **options):
        days = options["days"]
        filter_sources = options["filter_sources"]
        limit = options["limit"]
        save_to_db = options["save"]
        context_val = options["context"]
        fomc_time_str = options["fomc_time"]

        fomc_time = None
        if fomc_time_str:
            from django.utils.dateparse import parse_datetime

            fomc_time = parse_datetime(fomc_time_str)
            if fomc_time and timezone.is_naive(fomc_time):
                fomc_time = timezone.make_aware(fomc_time)

        self.stdout.write(self.style.HTTP_INFO("=" * 50))
        self.stdout.write(self.style.HTTP_INFO("🧪 DN-MAS Pipeline Test"))
        self.stdout.write(self.style.HTTP_INFO("=" * 50))

        # Step 1: Get articles from DB
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        self.stdout.write(f"\n📅 Date range: {start_date.date()} to {end_date.date()}")

        articles_qs = get_articles_from_db(
            start_date, end_date, filter_sources
        ).order_by("published_at")
        articles_list = list(articles_qs[:limit])

        if not articles_list:
            self.stdout.write(self.style.WARNING("⚠️  No articles found."))
            return

        self.stdout.write(self.style.SUCCESS(f"✅ Found {len(articles_list)} articles"))

        # Step 2: Format articles for agent
        formatted = format_articles_for_agent(articles_list)
        idx_to_metadata = create_idx_to_metadata_map(formatted.get_metadata_list())

        initial_state = {
            "articles": formatted.to_llm_dict(),
            "context": "those are fomc articles",
        }

        # Step 3: Run the agent pipeline
        self.stdout.write("\n🤖 Running DN-MAS pipeline...")

        try:
            final_state = asyncio.run(dn_mas_runner(initial_state))

            if "summary_with_citations" in final_state:
                # 1. RAW Agent Output (Indices)
                raw_result = SummaryWithCitations(
                    **final_state["summary_with_citations"]
                )

                # 2. ENRICHED App Model (UUIDs + Metadata)
                enriched_summary = enrich_summary_to_app_model(
                    raw_result, idx_to_metadata
                )

                self.stdout.write("\n" + "=" * 60)
                self.stdout.write(self.style.HTTP_INFO("📝 SUMMARY WITH CITATIONS"))
                self.stdout.write("=" * 60)

                # Print Summary
                self.stdout.write(self.style.SUCCESS("\n📄 Summary Text:"))
                self.stdout.write(enriched_summary.summary_text)

                # Print Citations
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n🔗 Citations ({len(enriched_summary.citations)} total):"
                    )
                )

                for i, citation in enumerate(enriched_summary.citations, 1):
                    self.stdout.write(f'\n[{i}] "{citation.summary_sentence}"')
                    for source in citation.sources:
                        expert = (
                            f" ({source.expert_name})" if source.expert_name else ""
                        )
                        self.stdout.write(
                            f"    └── {source.article_source}: {source.article_title}{expert}"
                        )
                        self.stdout.write(
                            f"        URL: {source.article_url} | UUID: {source.article_uuid}"
                        )

                self.stdout.write("\n" + "=" * 60)

                # Save to database
                if save_to_db:
                    self.stdout.write("\n💾 Saving to database...")
                    summary_obj = save_dn_mas_summary(
                        enriched_summary=enriched_summary,
                        articles_list=articles_list,
                        start_date=start_date,
                        end_date=end_date,
                        agent_name="test_dn_mas",
                        context=context_val,
                        fomc_announcement_datetime=fomc_time,
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Saved Summary: {summary_obj.uuid}")
                    )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Pipeline failed: {str(e)}"))
            import traceback

            self.stdout.write(traceback.format_exc())
