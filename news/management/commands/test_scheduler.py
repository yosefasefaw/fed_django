from datetime import datetime, timedelta, timezone as dt_timezone
from django.core.management.base import BaseCommand
from django.utils import timezone
from news.models import FetchLog
from news.utils import  is_in_fomc_critical_window
from news.services import retrieve_articles, save_articles
import time
from news.selectors import get_articles_from_db
from multi_agent_systems.helpers import (
    format_articles_for_agent,
    create_idx_to_metadata_map,
    enrich_summary_to_app_model,
)
from multi_agent_systems.dn_mas.runner import dn_mas_runner
from multi_agent_systems.dn_mas.schemas import SummaryWithCitations
from multi_agent_systems.st_mas.runner import st_mas_runner
from multi_agent_systems.st_mas.schemas import convert_topic_analysis_indexes_to_uuids
from multi_agent_systems.services import save_dn_mas_summary, save_st_mas_collection
import asyncio


class Command(BaseCommand):
    help = "Test scheduler command triggering both DN-MAS and ST-MAS pipelines"

    def add_arguments(self, parser):
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
        parser.add_argument(
            "--hours",
            type=int,
            default=24,
            help="Number of hours of articles to fetch and analyze",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=2,
            help="Maximum number of articles to process",
        )
        parser.add_argument(
            "--now",
            type=str,
            default=None,
            help="Override current time (e.g., '2025-12-18 14:00')",
        )
        parser.add_argument(
            "--articles-count",
            type=int,
            default=100,
            help="Number of articles to fetch and analyze",
        )
        parser.add_argument(
            "--page-numbers",
            type=int,
            default=2,
            help="Number of pages to fetch and analyze",
        )

    def handle(self, *args, **options):
        # Time setup
        if options["now"]:
            fmt = "%Y-%m-%d %H:%M"
            dt = datetime.strptime(options["now"], fmt)
            now = timezone.make_aware(dt, dt_timezone.utc)
        else:
            now = timezone.now()

        context_str = options["context"]
        fomc_time = options["fomc_time"]
        hours = options["hours"]
        limit = options["limit"]
        articles_count = options["articles_count"]
        page_numbers = options["page_numbers"]
        msg = f"RUNNING: Manual/Scheduler Trigger at {now.strftime('%H:%M:%S')}"
        self.stdout.write(self.style.SUCCESS(msg))

        # Calculate unified start time
        start_date = now - timedelta(hours=hours)

        # Fetch and Save News
        try:
            # 1. Fetching news (using unified start_date)
            # Note: retrieve_articles expects start/end dates
            articles = retrieve_articles(
                date_start=start_date,
                date_end=now,
                articles_count=articles_count,
                page_numbers=page_numbers,
            )
            new_saved, updated = save_articles(articles)

            self.stdout.write(
                self.style.MIGRATE_LABEL(
                    f"   ∟ Data Sync Complete: {new_saved} new, {updated} updated."
                )
            )

            # 2. Pipeline Trigger (Wait for DB to settle)
            time.sleep(10)

            # Retrieve articles for agent (using SAME unified start_date)
            # articles_qs = get_articles_from_db(start_date, end_date) -> end_date is now
            end_date = now
            db_lookup_start_time = end_date-timedelta(hours=10)
            articles_qs = get_articles_from_db(db_lookup_start_time, end_date)
            articles_list = list(articles_qs[:limit])

            self.stdout.write(
                f"   ∟ Agent Query: Found {len(articles_list)} articles in DB for range {db_lookup_start_time.strftime('%Y-%m-%d %H:%M')} to {now.strftime('%Y-%m-%d %H:%M')}"
            )

            if articles_list:
                # Shared Prep
                formatted = format_articles_for_agent(articles_list)
                metadata_list = formatted.get_metadata_list()
                idx_to_metadata = create_idx_to_metadata_map(metadata_list)

                initial_state = {
                    "articles": formatted.to_llm_dict(),
                    "context": f"Automated scheduler run at {now.strftime('%Y-%m-%d %H:%M')}",
                }

                # --- RUN DN-MAS ---
                self.stdout.write(
                    self.style.SUCCESS(
                        f"   ∟ Triggering DN-MAS with {len(articles_list)} articles..."
                    )
                )
                dn_final_state = asyncio.run(dn_mas_runner(initial_state))

                if "summary_with_citations" in dn_final_state:
                    raw_result = SummaryWithCitations(
                        **dn_final_state["summary_with_citations"]
                    )
                    enriched_summary = enrich_summary_to_app_model(
                        raw_result, idx_to_metadata
                    )

                    summary_obj = save_dn_mas_summary(
                        enriched_summary=enriched_summary,
                        articles_list=articles_list,
                        start_date=start_date,
                        end_date=end_date,
                        agent_name="scheduler",
                        context=context_str,
                        fomc_announcement_datetime=fomc_time,
                        created_at = now,
                        
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"     ✅ DN-MAS Complete: Saved Summary {summary_obj.uuid}"
                        )
                    )

                # --- RUN ST-MAS ---
                self.stdout.write(
                    self.style.SUCCESS(
                        f"   ∟ Triggering ST-MAS (Parallel Topics)..."
                    )
                )
                st_final_state = asyncio.run(st_mas_runner(initial_state))

                # Convert labels to metadata
                topic_collection = convert_topic_analysis_indexes_to_uuids(
                    llm_output=st_final_state, article_uuids=metadata_list
                )

                group_obj = save_st_mas_collection(
                    collection=topic_collection,
                    articles_list=articles_list,
                    agent_name="scheduler",
                    context=context_str,
                    fomc_announcement_datetime=fomc_time,
                    created_at = now,
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"     ✅ ST-MAS Complete: Saved Group {group_obj.uuid} ({len(topic_collection.topics)} topics)"
                    )
                )

            # log_msg = f"{msg} | Fetched: {len(articles)}, New: {new_saved}, Updated: {updated}"
            # FetchLog.objects.create(message=log_msg)

        except Exception as e:
            error_msg = f"FAILED Pipeline at {now.strftime('%H:%M:%S')}: {str(e)}"
            self.stdout.write(self.style.ERROR(f"   ∟ {error_msg}"))
            import traceback

            self.stdout.write(traceback.format_exc())
            FetchLog.objects.create(message=error_msg)
