from django.db import models


class RulesDailyJobLog(models.Model):
    created_dt = models.DateTimeField(
        auto_now_add=True, blank=True, null=True, verbose_name="Created at", db_index=True
    )
