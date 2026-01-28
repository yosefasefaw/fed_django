from django.contrib import admin
from .models import (
    Summary, Citation, CitationSource,
    TopicAnalysisGroup, TopicAnalysis, TopicMetric, 
    TopicExpert, TopicCitation, TopicCitationSource
)

# --- DN-MAS Admin ---

@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = ("uuid", "created_at", "article_count", "agent_name")
    list_filter = ("agent_name", "created_at")
    search_fields = ("uuid", "summary_text")
    readonly_fields = ("uuid", "created_at")
    
    fieldsets = (
        ("Summary", {
            "fields": ("uuid", "summary_text")
        }),
        ("Metadata", {
            "fields": ("created_at", "article_count", "date_range_start", "date_range_end", "agent_name")
        }),
    )


@admin.register(Citation)
class CitationAdmin(admin.ModelAdmin):
    list_display = ("summary", "order", "summary_sentence_preview")
    list_filter = ("summary",)
    search_fields = ("summary_sentence",)
    
    def summary_sentence_preview(self, obj):
        return obj.summary_sentence[:80] + "..." if len(obj.summary_sentence) > 80 else obj.summary_sentence
    summary_sentence_preview.short_description = "Sentence"


@admin.register(CitationSource)
class CitationSourceAdmin(admin.ModelAdmin):
    list_display = ("citation", "article_source", "expert_name", "sentence_preview")
    list_filter = ("article_source",)
    search_fields = ("sentence", "article_title", "expert_name")
    
    def sentence_preview(self, obj):
        return obj.sentence[:60] + "..." if len(obj.sentence) > 60 else obj.sentence
    sentence_preview.short_description = "Quote"


# --- ST-MAS Admin ---

@admin.register(TopicAnalysisGroup)
class TopicAnalysisGroupAdmin(admin.ModelAdmin):
    list_display = ("uuid", "created_at")
    readonly_fields = ("uuid", "created_at")


@admin.register(TopicAnalysis)
class TopicAnalysisAdmin(admin.ModelAdmin):
    list_display = ("topic_name", "sentiment", "group", "created_at")
    list_filter = ("topic_name", "sentiment", "created_at")


@admin.register(TopicMetric)
class TopicMetricAdmin(admin.ModelAdmin):
    list_display = ("name", "value", "topic_analysis", "sentiment")
    list_filter = ("sentiment", "topic_analysis")


@admin.register(TopicExpert)
class TopicExpertAdmin(admin.ModelAdmin):
    list_display = ("expert_name", "organization", "topic_analysis", "sentiment")
    list_filter = ("sentiment", "topic_analysis")


@admin.register(TopicCitation)
class TopicCitationAdmin(admin.ModelAdmin):
    list_display = ("topic_analysis", "metric", "expert", "summary_sentence_preview")
    
    def summary_sentence_preview(self, obj):
        return obj.summary_sentence[:80] + "..." if len(obj.summary_sentence) > 80 else obj.summary_sentence


@admin.register(TopicCitationSource)
class TopicCitationSourceAdmin(admin.ModelAdmin):
    list_display = ("topic_citation", "article_source", "expert_name", "sentence_preview")
    
    def sentence_preview(self, obj):
        return obj.sentence[:60] + "..." if len(obj.sentence) > 60 else obj.sentence
