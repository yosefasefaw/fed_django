from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, TemplateView, DetailView
from django.views import View
from itertools import chain
from operator import attrgetter
from .models import Summary, TopicAnalysisGroup


class SummaryListView(ListView):
    model = Summary
    template_name = "multi_agent_systems/summary_list.html"
    context_object_name = "summaries"
    ordering = ["-created_at"]


class ReportBoxView(TemplateView):
    """Combined view showing both DN-MAS Summaries and ST-MAS Topic Analyses in one table."""

    template_name = "multi_agent_systems/report_box.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Fetch both types
        summaries = list(Summary.objects.all())
        analyses = list(TopicAnalysisGroup.objects.all())

        # Add a type marker to each object
        for s in summaries:
            s.report_type = "summary"
        for a in analyses:
            a.report_type = "analysis"

        # Combine and sort by created_at (newest first)
        combined = sorted(
            chain(summaries, analyses), key=attrgetter("created_at"), reverse=True
        )[:20]  # Limit to 20 most recent

        context["reports"] = combined
        return context


class SummaryDetailView(DetailView):
    """Display a single summary with full text and citations."""

    model = Summary
    template_name = "multi_agent_systems/summary_detail.html"
    context_object_name = "summary"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        return Summary.objects.prefetch_related("citations__sources")


class LatestSummaryRedirectView(View):
    """Redirect to the latest summary, or show empty state if none exist."""

    def get(self, request):
        latest = Summary.objects.order_by("-created_at").first()
        if latest:
            return redirect("multi_agent_systems:summary_detail", uuid=latest.uuid)
        else:
            return render(request, "multi_agent_systems/summary_empty.html")
