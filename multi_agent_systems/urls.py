from django.urls import path
from .views import (
    SummaryListView,
    ReportBoxView,
    SummaryDetailView,
    LatestSummaryRedirectView,
)

app_name = "multi_agent_systems"

urlpatterns = [
    path("summaries/", SummaryListView.as_view(), name="summary_list"),
    path("report-box/", ReportBoxView.as_view(), name="report_box"),
    path("summary/", LatestSummaryRedirectView.as_view(), name="latest_summary"),
    path("summary/<uuid:uuid>/", SummaryDetailView.as_view(), name="summary_detail"),
]
