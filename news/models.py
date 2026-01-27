import uuid
from django.db import models

class Source(models.Model):
    uri = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    data_type = models.CharField(max_length=50, null=True, blank=True)
    image = models.URLField(max_length=1000, null=True, blank=True)

    def __str__(self):
        return self.title or self.uri

class Article(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Identifiers
    uri = models.CharField(max_length=255, unique=True)
    url = models.URLField(max_length=1000, null=True, blank=True)
    
    # Content
    title = models.CharField(max_length=500, null=True, blank=True)
    body = models.TextField(null=True, blank=True)
    lang = models.CharField(max_length=10, null=True, blank=True)
    data_type = models.CharField(max_length=20, null=True, blank=True) # news, blog, pr
    
    # Relationship
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='articles', null=True, blank=True)
    
    # Enrichment
    sentiment = models.FloatField(null=True, blank=True)
    relevance = models.IntegerField(default=0, null=True, blank=True)
    image = models.URLField(max_length=1000, null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Flattened Data (JSON)
    authors = models.JSONField(default=list, blank=True, null=True) 
    concepts = models.JSONField(default=list, blank=True, null=True)
    categories = models.JSONField(default=list, blank=True, null=True)
    raw_data = models.JSONField(null=True, blank=True) # Full backup

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.title or self.uri

class FetchLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.timestamp} - {self.message}"
