import uuid
from django.db import models

from news.models import Article


class Summary(models.Model):
    """
    Stores the generated summary from the DN-MAS pipeline.
    """

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # The summary text
    summary_text = models.TextField()

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    # Processing info
    article_count = models.IntegerField(default=0, help_text="Number of articles used")
    date_range_start = models.DateTimeField(null=True, blank=True)
    date_range_end = models.DateTimeField(null=True, blank=True)

    # Agent info
    agent_name = models.TextField(default="dn_mas")

    # All articles provided to the agent (input)
    articles_provided = models.ManyToManyField(
        Article,
        related_name="summaries_as_input",
        blank=True,
        help_text="All articles provided to the agent for processing",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Summaries"

    def __str__(self):
        return f"Summary {self.uuid} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

    @property
    def articles_used(self):
        """Returns articles that were actually cited in the summary."""
        from django.db.models import Q

        cited_article_ids = (
            CitationSource.objects.filter(citation__summary=self, article__isnull=False)
            .values_list("article_id", flat=True)
            .distinct()
        )
        return Article.objects.filter(id__in=cited_article_ids)

    @property
    def articles_provided_count(self):
        return self.articles_provided.count()

    @property
    def articles_used_count(self):
        return self.articles_used.count()


class Citation(models.Model):
    """
    A citation linking a summary sentence to its source articles.
    """

    summary = models.ForeignKey(
        Summary, on_delete=models.CASCADE, related_name="citations"
    )

    # The sentence from the summary that needs citation
    summary_sentence = models.TextField()

    # Order in the summary
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"Citation {self.order}: {self.summary_sentence[:50]}..."


class CitationSource(models.Model):
    """
    A specific source/quote backing up a citation.
    Links to the actual Article model.
    """

    citation = models.ForeignKey(
        Citation, on_delete=models.CASCADE, related_name="sources"
    )

    # Link to the actual article
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="citation_sources",
        null=True,
        blank=True,
    )

    # The sentence/quote from the article
    sentence = models.TextField()

    # Expert name if mentioned
    expert_name = models.TextField(null=True, blank=True)

    # Denormalized article info (for display without joins)
    article_uuid = models.TextField()
    article_source = models.TextField(null=True, blank=True)
    article_title = models.TextField(null=True, blank=True)
    article_url = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Source: {self.article_source} - {self.sentence[:30]}..."


# --- ST-MAS (Static Topic MAS) Models ---


class TopicAnalysisGroup(models.Model):
    """
    Parent container for a collection of topic analyses (ST-MAS run).
    """

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    agent_name = models.TextField(default="st_mas")
    context = models.CharField(
        max_length=50,
        default="general",
        help_text="Analysis context: pre_announcement, post_announcement, general",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Articles used for this whole run
    articles_provided = models.ManyToManyField(
        Article, related_name="topic_analysis_groups"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Topic Analysis Groups"

    def __str__(self):
        return f"Analysis Group {self.uuid} ({self.created_at.strftime('%Y-%m-%d')})"


class TopicAnalysis(models.Model):
    """
    A specific topic analysis (e.g., Housing, Inflation) within a group.
    """

    group = models.ForeignKey(
        TopicAnalysisGroup, on_delete=models.CASCADE, related_name="topics"
    )
    topic_name = models.TextField()  # Housing, Labor, etc.
    sentiment = models.CharField(max_length=20)  # hawkish, dovish, neutral
    summary_text = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Topic Analyses"

    def __str__(self):
        return f"{self.topic_name} Analysis ({self.sentiment})"


class TopicMetric(models.Model):
    """Metrics extracted for a specific topic analysis."""

    topic_analysis = models.ForeignKey(
        TopicAnalysis, on_delete=models.CASCADE, related_name="metrics"
    )
    name = models.TextField()
    value = models.TextField()
    period = models.TextField()
    discussion = models.TextField()
    sentiment = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.name}: {self.value}"


class TopicExpert(models.Model):
    """Expert opinions extracted for a specific topic analysis."""

    topic_analysis = models.ForeignKey(
        TopicAnalysis, on_delete=models.CASCADE, related_name="experts"
    )
    expert_name = models.TextField()
    organization = models.TextField()
    opinion = models.TextField()
    sentiment = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.expert_name} ({self.organization})"


class TopicCitation(models.Model):
    """
    Citations for ST-MAS. Can link to a TopicAnalysis summary,
    a TopicMetric discussion, or a TopicExpert opinion.
    """

    # Link to one of these
    topic_analysis = models.ForeignKey(
        TopicAnalysis,
        on_delete=models.CASCADE,
        related_name="summary_citations",
        null=True,
        blank=True,
    )
    metric = models.ForeignKey(
        TopicMetric,
        on_delete=models.CASCADE,
        related_name="citations",
        null=True,
        blank=True,
    )
    expert = models.ForeignKey(
        TopicExpert,
        on_delete=models.CASCADE,
        related_name="citations",
        null=True,
        blank=True,
    )

    summary_sentence = models.TextField()
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"Topic Citation: {self.summary_sentence[:50]}..."


class TopicCitationSource(models.Model):
    """The source article/quote for a TopicCitation."""

    topic_citation = models.ForeignKey(
        TopicCitation, on_delete=models.CASCADE, related_name="sources"
    )

    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="topic_citation_sources",
        null=True,
        blank=True,
    )

    sentence = models.TextField()
    expert_name = models.TextField(null=True, blank=True)
    article_uuid = models.TextField()
    article_source = models.TextField(null=True, blank=True)
    article_title = models.TextField(null=True, blank=True)
    article_url = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Topic Source from {self.article_source}"
