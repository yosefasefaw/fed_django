"""
Management command to test the ST-MAS (Static Topic Multi-Agent System) pipeline.
"""

import asyncio
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from news.selectors import get_articles_from_db
from multi_agent_systems.helpers import (
    format_articles_for_agent,
    create_idx_to_metadata_map,
)
from multi_agent_systems.st_mas.runner import st_mas_runner
from multi_agent_systems.st_mas.schemas import (
    convert_topic_analysis_indexes_to_uuids,
    print_topic_summary,
)
from multi_agent_systems.services import save_st_mas_collection


class Command(BaseCommand):
    help = "Test the ST-MAS agent pipeline with articles from the database"

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
            help="Save the analysis collection to the database",
        )
        parser.add_argument(
            "--context",
            type=str,
            default="general",
            help="Context for the analysis (pre_announcement, post_announcement, general)",
        )

    def handle(self, *args, **options):
        days = options["days"]
        filter_sources = options["filter_sources"]
        limit = options["limit"]
        save_to_db = options["save"]

        self.stdout.write(self.style.HTTP_INFO("=" * 50))
        self.stdout.write(self.style.HTTP_INFO("🧪 ST-MAS Pipeline Test"))
        self.stdout.write(self.style.HTTP_INFO("=" * 50))

        # Step 1: Get articles from DB
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        self.stdout.write(f"\n📅 Date range: {start_date.date()} to {end_date.date()}")

        articles_qs = get_articles_from_db(start_date, end_date, filter_sources)
        articles_list = list(articles_qs[:limit])

        if not articles_list:
            self.stdout.write(self.style.WARNING("⚠️  No articles found."))
            return

        self.stdout.write(self.style.SUCCESS(f"✅ Found {len(articles_list)} articles"))

        # Step 2: Format articles for agent
        formatted = format_articles_for_agent(articles_list)
        metadata_list = formatted.get_metadata_list()

        initial_state = {
            "articles": formatted.to_llm_dict(),
            "context": "those are fomc articles",
        }

        # Step 3: Run the agent pipeline
        self.stdout.write("\n🤖 Running ST-MAS pipeline...")
        self.stdout.write(
            self.style.WARNING(
                "   (This analysis covers multiple topics in parallel, it might take a moment)"
            )
        )

        try:
            # 1. Run the agent
            final_state = asyncio.run(st_mas_runner(initial_state))

            # 2. Convert indices to UUIDs and enrich with metadata
            topic_analysis_collection = convert_topic_analysis_indexes_to_uuids(
                llm_output=final_state, article_uuids=metadata_list
            )

            self.stdout.write(self.style.SUCCESS("\n✅ Pipeline completed!"))

            # 3. Print Results
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write(
                self.style.HTTP_INFO("📝 DETAILED TOPIC ANALYSIS RESULTS")
            )
            self.stdout.write("=" * 60)

            for topic_name, analysis in topic_analysis_collection.items():
                print_topic_summary(analysis, topic_name=topic_name)

            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✅ Total topics analyzed: {len(topic_analysis_collection.topics)}"
                )
            )

            # 4. Save to database if requested
            if save_to_db:
                self.stdout.write("\n💾 Saving collection to database...")
                group_obj = save_st_mas_collection(
                    collection=topic_analysis_collection,
                    articles_list=articles_list,
                    agent_name="test_st_mas",
                    context=options.get("context", "general"),
                )
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Saved Analysis Group: {group_obj.uuid}")
                )
                self.stdout.write(
                    self.style.HTTP_INFO(
                        f"   ∟ contains {len(topic_analysis_collection.topics)} topics."
                    )
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Pipeline failed: {str(e)}"))
            import traceback

            self.stdout.write(traceback.format_exc())
