from django.db import models

import dash.constants


class ContentAdSourceQuerySet(models.QuerySet):
    def filter_by_sources(self, sources):
        return self.filter(source__in=sources)

    def exclude_display(self, show_display=False):
        if show_display:
            return self
        return self.exclude(content_ad__ad_group__campaign__type=dash.constants.CampaignType.DISPLAY)
