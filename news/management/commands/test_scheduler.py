from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from news.models import FetchLog
from news.utils import is_in_mock_critical_window
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

    def handle(self, *args, **options):
        now = timezone.now()

        # Call the MOCK utility function for testing!
        is_critical = is_in_mock_critical_window(now)

        should_run = False
        reason = ""

        if is_critical:
            # During mock "critical" window, we run every time we are called
            should_run = True
            reason = "Inside MOCK critical minute (5-min interval)"
        else:
            # Outside critical window: Only run if it's an even minute (for testing)
            if now.minute % 2 == 0:
                should_run = True
                reason = "Normal test interval (Even minute)"

        if should_run:
            msg = f"RUNNING: {reason} at {now.strftime('%H:%M:%S')}"
            self.stdout.write(self.style.SUCCESS(msg))

            # Fetch and Save News
            try:
                # 1. Fetching news
                date_start = now - timedelta(hours=1)
                articles = retrieve_articles(
                    date_start=date_start, date_end=now, articles_count=5
                )
                new_saved, updated = save_articles(articles)

                self.stdout.write(
                    self.style.MIGRATE_LABEL(
                        f"   ∟ Data Sync Complete: {new_saved} new, {updated} updated."
                    )
                )

                # 2. Pipeline Trigger (Wait for DB to settle)
                time.sleep(2)

                # Retrieve articles for agent
                start_date = now - timedelta(days=1)
                end_date = now
                limit = 5

                articles_qs = get_articles_from_db(start_date, end_date)
                articles_list = list(articles_qs[:limit])

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
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"     ✅ ST-MAS Complete: Saved Group {group_obj.uuid} ({len(topic_collection.topics)} topics)"
                        )
                    )

                log_msg = f"{msg} | Fetched: {len(articles)}, New: {new_saved}, Updated: {updated}"
                FetchLog.objects.create(message=log_msg)

            except Exception as e:
                error_msg = f"FAILED Pipeline at {now.strftime('%H:%M:%S')}: {str(e)}"
                self.stdout.write(self.style.ERROR(f"   ∟ {error_msg}"))
                import traceback

                self.stdout.write(traceback.format_exc())
                FetchLog.objects.create(message=error_msg)
        else:
            self.stdout.write(
                f"SKIPPING: (Critical Window: {is_critical}) at {now.strftime('%H:%M:%S')}"
            )
