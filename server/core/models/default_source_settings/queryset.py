from django.db import models


class DefaultSourceSettingsQuerySet(models.QuerySet):
    def with_credentials(self):
        return self.exclude(credentials__isnull=True)
