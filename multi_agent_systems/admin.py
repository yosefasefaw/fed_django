from django.contrib import admin
from .models import Summary, Citation, CitationSource


class CitationSourceInline(admin.TabularInline):
    model = CitationSource
    extra = 0
    readonly_fields = ("article", "sentence", "expert_name", "article_uuid", "article_source", "article_title", "article_url")


class CitationInline(admin.TabularInline):
    model = Citation
    extra = 0
    readonly_fields = ("summary_sentence", "order")
    show_change_link = True


@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = ("uuid", "created_at", "article_count", "agent_name")
    list_filter = ("agent_name", "created_at")
    search_fields = ("uuid", "summary_text")
    readonly_fields = ("uuid", "created_at")
    inlines = [CitationInline]
    
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
    inlines = [CitationSourceInline]
    
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
