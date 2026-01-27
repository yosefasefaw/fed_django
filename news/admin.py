from django.contrib import admin
from .models import Source, Article, FetchLog

@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'uri', 'data_type')
    search_fields = ('title', 'uri')

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'published_at', 'colored_sentiment', 'lang')
    list_filter = ('source', 'lang', 'published_at')
    search_fields = ('title', 'body')
    date_hierarchy = 'published_at'
    
    def colored_sentiment(self, obj):
        if obj.sentiment is None:
            return "-"
        
        # Rounding for clean display
        score = round(obj.sentiment, 2)
        
        # Adding some color for better UX
        color = "green" if score > 0 else "red" if score < 0 else "gray"
        from django.utils.html import format_html
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, score)
    
    colored_sentiment.short_description = 'Sentiment'

@admin.register(FetchLog)
class FetchLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'message')
    readonly_fields = ('timestamp',)
