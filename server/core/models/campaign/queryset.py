from django.db import models
from django.db.models import Exists
from django.db.models import OuterRef

import core.models
import zemauth.features.entity_permission.shortcuts
import zemauth.models


class CampaignQuerySet(zemauth.features.entity_permission.shortcuts.HasEntityPermissionQuerySetMixin, models.QuerySet):
    def filter_by_sources(self, sources):
        if not core.models.helpers.should_filter_by_sources(sources):
            return self

        return self.filter(adgroup__adgroupsource__source__in=sources).distinct()

    def filter_by_agencies(self, agencies):
        if not agencies:
            return self
        return self.filter(account__agency__in=agencies)

    def filter_by_account_types(self, account_types):
        if not account_types:
            return self
        return self.filter(account__settings__account_type__in=account_types)

    def exclude_archived(self, show_archived=False):
        if show_archived:
            return self
        return self.exclude(archived=True)

    def filter_active(self):
        import automation.campaignstop

        # NOTE: has to be at the end because it has to do a separate query and thus evaluates the queryset
        campaignstop_states = automation.campaignstop.get_campaignstop_states(self)
        active_ids = []
        for campaign_id, campaignstop_state in campaignstop_states.items():
            if campaignstop_state["allowed_to_run"]:
                active_ids.append(campaign_id)
        return self.filter(id__in=active_ids)

    def filter_has_active_ad_groups(self):
        active_ad_groups_subquery = core.models.ad_group.AdGroup.objects.filter_current_and_active().filter(
            campaign=OuterRef("id")
        )
        return self.annotate(active_ad_groups=Exists(active_ad_groups_subquery)).filter(active_ad_groups=True)

    def _get_query_path_to_account(self) -> str:
        return "account"
