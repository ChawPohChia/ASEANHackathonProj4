from django.db import models


class XPost(models.Model):
    """Original X (Twitter) post payload for audit and display."""

    post_id = models.CharField(max_length=32, unique=True, db_index=True)
    text = models.TextField()
    author_id = models.CharField(max_length=32, blank=True)
    author_username = models.CharField(max_length=255, blank=True)
    lang = models.CharField(max_length=16, blank=True)
    post_created_at = models.DateTimeField(
        help_text="Created time from X (UTC stored with timezone).",
    )
    fetched_at = models.DateTimeField(auto_now_add=True)
    raw_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-post_created_at"]
        verbose_name = "X post"
        verbose_name_plural = "X posts"

    def __str__(self) -> str:
        return f"@{self.author_username or self.author_id}: {self.text[:50]}"


class SentimentAnalysis(models.Model):
    """LLM-derived weather sentiment for a stored post."""

    post = models.OneToOneField(
        XPost,
        on_delete=models.CASCADE,
        related_name="sentiment",
    )
    score = models.PositiveSmallIntegerField(
        help_text="0 = very unhappy … 4 = neutral … 9 = extremely happy (weather-related).",
    )
    model_name = models.CharField(max_length=128)
    prompt_version = models.CharField(max_length=64)
    rationale = models.TextField(blank=True)
    classified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-classified_at"]
        verbose_name = "sentiment analysis"
        verbose_name_plural = "sentiment analyses"

    def __str__(self) -> str:
        return f"{self.score} for {self.post.post_id}"
