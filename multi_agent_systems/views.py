from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, TemplateView, DetailView
from django.views import View
from itertools import chain
from operator import attrgetter
from .models import Summary, TopicAnalysisGroup, TopicAnalysis


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        summary = self.object

        # Navigation: Get previous and next summaries based on created_at
        context["prev_summary"] = Summary.objects.filter(
            created_at__lt=summary.created_at
        ).order_by("-created_at").first()

        context["next_summary"] = Summary.objects.filter(
            created_at__gt=summary.created_at
        ).order_by("created_at").first()

        # FOMC Timing Context
        context["timing_focus"] = summary.get_timing_focus
        context["timing_delta"] = summary.get_timing_delta

        return context

    def get_queryset(self):
        return Summary.objects.prefetch_related("citations__sources")


class TopicAnalysisGroupDetailView(DetailView):
    """Display a grid overview of topic analyses within a group."""

    model = TopicAnalysisGroup
    template_name = "multi_agent_systems/topic_analysis_detail.html"
    context_object_name = "group"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.object

        # Navigation: Get previous and next groups based on created_at
        context["prev_group"] = TopicAnalysisGroup.objects.filter(
            created_at__lt=group.created_at
        ).order_by("-created_at").first()
        
        context["next_group"] = TopicAnalysisGroup.objects.filter(
            created_at__gt=group.created_at
        ).order_by("created_at").first()

        # FOMC Timing Context
        context["timing_focus"] = group.get_timing_focus
        context["timing_delta"] = group.get_timing_delta

        # Sort all topics alphabetically first
        all_topics = sorted(list(group.topics.all()), key=lambda t: t.topic_name)

        # Group by sentiment
        context["dovish_topics"] = [
            t for t in all_topics if t.sentiment.lower() == "dovish"
        ]
        context["neutral_topics"] = [
            t for t in all_topics if t.sentiment.lower() == "neutral"
        ]
        context["hawkish_topics"] = [
            t for t in all_topics if t.sentiment.lower() == "hawkish"
        ]

        return context

    def get_queryset(self):
        return TopicAnalysisGroup.objects.prefetch_related("topics")


class TopicDetailView(DetailView):
    """Deep-dive view for a specific TopicAnalysis."""

    model = TopicAnalysis
    template_name = "multi_agent_systems/topic_detail.html"
    context_object_name = "topic"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        topic = self.object

        # Get all metrics and experts with citations prefetched
        metrics = list(topic.metrics.all())
        experts = list(topic.experts.all())

        # Hero metrics: top 3 metrics for the stat-banner
        context["hero_metrics"] = metrics[:3]

        # Group metrics by stance
        context["dovish_metrics"] = [
            m for m in metrics if m.sentiment.lower() == "dovish"
        ]
        context["neutral_metrics"] = [
            m for m in metrics if m.sentiment.lower() == "neutral"
        ]
        context["hawkish_metrics"] = [
            m for m in metrics if m.sentiment.lower() == "hawkish"
        ]

        # Group experts by stance
        context["dovish_experts"] = [
            e for e in experts if e.sentiment.lower() == "dovish"
        ]
        context["neutral_experts"] = [
            e for e in experts if e.sentiment.lower() == "neutral"
        ]
        context["hawkish_experts"] = [
            e for e in experts if e.sentiment.lower() == "hawkish"
        ]

        return context

    def get_queryset(self):
        return TopicAnalysis.objects.prefetch_related(
            "metrics",
            "experts",
            "summary_citations__sources",
            "metrics__citations__sources",
            "experts__citations__sources",
        )


class LatestTopicAnalysisRedirectView(View):
    """Redirect to the latest topic analysis group."""

    def get(self, request):
        latest = TopicAnalysisGroup.objects.order_by("-created_at").first()
        if latest:
            return redirect("multi_agent_systems:topic_analysis_detail", uuid=latest.uuid)
        else:
            return render(request, "multi_agent_systems/topic_analysis_empty.html")


class LatestSummaryRedirectView(View):
    """Redirect to the latest summary, or show empty state if none exist."""

    def get(self, request):
        latest = Summary.objects.order_by("-created_at").first()
        if latest:
            return redirect("multi_agent_systems:summary_detail", uuid=latest.uuid)
        else:
            return render(request, "multi_agent_systems/summary_empty.html")
