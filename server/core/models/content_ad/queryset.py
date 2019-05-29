from django.db import models

import core.models.helpers
from dash import constants


class ContentAdQuerySet(models.QuerySet):
    def filter_by_user(self, user):
        if user.has_perm("zemauth.can_see_all_accounts"):
            return self
        return self.filter(
            models.Q(ad_group__campaign__account__users__id=user.id)
            | models.Q(ad_group__campaign__account__agency__users__id=user.id)
        ).distinct()

    def filter_by_sources(self, sources):
        if not core.models.helpers.should_filter_by_sources(sources):
            return self

        content_ad_ids = (
            core.models.ContentAdSource.objects.filter(source__in=sources)
            .select_related("content_ad")
            .distinct("content_ad_id")
            .values_list("content_ad_id", flat=True)
        )

        return self.filter(id__in=content_ad_ids)

    def exclude_archived(self, show_archived=False):
        if show_archived:
            return self
        return self.filter(archived=False)

    def exclude_display(self, show_display=False):
        if show_display:
            return self
        return self.exclude(ad_group__campaign__type=constants.CampaignType.DISPLAY)

    def filter_active(self):
        return self.filter(state=constants.ContentAdSourceState.ACTIVE)
