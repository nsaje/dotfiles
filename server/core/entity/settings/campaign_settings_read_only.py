# -*- coding: utf-8 -*-

import core.common
import core.entity.settings

from campaign_settings import CampaignSettings


class CampaignSettingsReadOnly(core.common.ReadOnlyModelMixin, CampaignSettings):
    """
    Read-only proxy for campaign settings that disables unnecessary history snapshots because
    they are not needed where we can guarantee no data will be modified.
    """

    SNAPSHOT_HISTORY = False

    class Meta(CampaignSettings.Meta):
        app_label = 'dash'
        proxy = True

    class QuerySet(core.common.ReadOnlyQuerySet, CampaignSettings.QuerySet):
        pass
