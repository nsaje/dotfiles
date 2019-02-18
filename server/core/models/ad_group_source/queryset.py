from django.db import models
from django.db.models import Q

import core.models.helpers
import dash.constants
import utils.dates_helper


class AdGroupSourceQuerySet(models.QuerySet):
    def filter_by_sources(self, sources):
        if not core.models.helpers.should_filter_by_sources(sources):
            return self

        return self.filter(source__in=sources)

    def filter_active(self):
        """
        Returns only ad groups sources that have settings set to active.
        """
        return self.filter(settings__state=dash.constants.AdGroupSourceSettingsState.ACTIVE)

    def filter_can_manage_content_ads(self):
        return self.filter(
            can_manage_content_ads=True,
            source_id__in=core.models.Source.objects.all().filter_can_manage_content_ads().values_list("id", flat=True),
        )

    def filter_running(self, date=None):
        if not date:
            date = utils.dates_helper.local_today()

        # circular dependency
        from automation.campaignstop import constants as campaignstop_constants

        return (
            self.filter_active()
            .filter(
                ad_group__settings__archived=False,
                ad_group__settings__state=dash.constants.AdGroupSettingsState.ACTIVE,
                ad_group__campaign__settings__archived=False,
                ad_group__settings__start_date__lte=date,
            )
            .filter(Q(ad_group__settings__end_date__gte=date) | Q(ad_group__settings__end_date__isnull=True))
            .filter(
                Q(
                    ad_group__campaign__real_time_campaign_stop=True,
                    ad_group__campaign__campaignstopstate__state=campaignstop_constants.CampaignStopState.ACTIVE,
                )
                | Q(ad_group__campaign__real_time_campaign_stop=False)
            )
        )
