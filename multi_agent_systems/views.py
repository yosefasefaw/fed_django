from django.shortcuts import render
from django.views.generic import ListView
from .models import Summary

class SummaryListView(ListView):
    model = Summary
    template_name = "multi_agent_systems/summary_list.html"
    context_object_name = "summaries"
    ordering = ["-created_at"]
