from django.urls import path
from .views import SummaryListView

app_name = "multi_agent_systems"

urlpatterns = [
    path("summaries/", SummaryListView.as_view(), name="summary_list"),
]
