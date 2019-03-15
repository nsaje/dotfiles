from django.db import models


class HistoryStacktrace(models.Model):
    class Meta:
        app_label = "dash"

    history = models.OneToOneField("History", related_name="stacktrace", on_delete=models.CASCADE)
    value = models.TextField()
